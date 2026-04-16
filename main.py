"""
Gemini 3.1 Flash TTS: prompt.txt を読み、音声を WAV として保存またはブラウザでダウンロード。
https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview
"""

from __future__ import annotations

import argparse
import html
import io
import os
import re
import sys
import time
import wave
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent
PROMPT_FILE = BASE_DIR / "prompt.txt"
MODEL_ID = "gemini-3.1-flash-tts-preview"
DEFAULT_VOICE = "Kore"
# プレビュー API が FinishReason.OTHER で音声パートなしを返すことがあるため再試行する
_TTS_MAX_ATTEMPTS = 5
_TTS_RETRY_BASE_SEC = 1.5


def _load_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key or not key.strip():
        raise RuntimeError(
            "環境変数 GEMINI_API_KEY（または GOOGLE_API_KEY）が設定されていません。"
            "プロジェクト直下の .env に GEMINI_API_KEY=... を記載してください。"
        )
    return key.strip()


def read_prompt_text() -> str:
    if not PROMPT_FILE.is_file():
        raise FileNotFoundError(f"見つかりません: {PROMPT_FILE}")
    text = PROMPT_FILE.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"{PROMPT_FILE} が空です。")
    return text.strip()


def _mime_sample_rate(mime_type: str | None) -> int:
    if not mime_type:
        return 24_000
    m = re.search(r"rate=(\d+)", mime_type, re.I)
    if m:
        return int(m.group(1))
    return 24_000


def _collect_pcm_from_response(
    response: types.GenerateContentResponse,
) -> tuple[bytes, int]:
    if not response.candidates:
        raise RuntimeError("応答に candidates がありません。")
    cand = response.candidates[0]
    if not cand.content or not cand.content.parts:
        raise RuntimeError("応答に音声パートがありません。")

    chunks: list[bytes] = []
    sample_rate: int | None = None
    for part in cand.content.parts:
        if not part.inline_data or not part.inline_data.data:
            continue
        chunks.append(part.inline_data.data)
        sr = _mime_sample_rate(part.inline_data.mime_type)
        sample_rate = sample_rate or sr

    if not chunks:
        raise RuntimeError("インライン音声データが返されませんでした。")
    return b"".join(chunks), sample_rate or 24_000


def pcm_to_wav_bytes(pcm: bytes, sample_rate: int, channels: int = 1, sample_width: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def synthesize_to_wav_bytes() -> bytes:
    prompt = read_prompt_text()
    voice = os.getenv("VOICE_NAME", DEFAULT_VOICE).strip() or DEFAULT_VOICE

    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
            )
        ),
    )

    # ラッパー Client を途中で GC させない（httpx が閉じてエラーになるのを防ぐ）
    client = genai.Client(api_key=_load_api_key())
    last_err: Exception | None = None
    for attempt in range(_TTS_MAX_ATTEMPTS):
        resp = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=cfg,
        )
        try:
            pcm, rate = _collect_pcm_from_response(resp)
            return pcm_to_wav_bytes(pcm, rate)
        except RuntimeError as e:
            last_err = e
            if attempt + 1 >= _TTS_MAX_ATTEMPTS:
                raise
            delay = _TTS_RETRY_BASE_SEC * (attempt + 1)
            time.sleep(delay)
    assert last_err is not None
    raise last_err


# --- CLI ---
def run_cli(output: Path | None) -> None:
    load_dotenv(BASE_DIR / ".env")
    wav = synthesize_to_wav_bytes()
    out = output or (BASE_DIR / f"gemini_tts_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.wav")
    out.write_bytes(wav)
    print(f"保存しました: {out}")


# --- Web ---
@asynccontextmanager
async def _lifespan(_app: FastAPI):
    load_dotenv(BASE_DIR / ".env")
    yield


app = FastAPI(title="Gemini TTS (prompt.txt)", lifespan=_lifespan)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    try:
        preview = html.escape(read_prompt_text())
    except Exception as e:
        preview = html.escape(f"(読み込みエラー: {e})")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="utf-8"/><title>Gemini TTS</title></head>
<body>
  <h1>Gemini 3.1 Flash TTS（prompt.txt）</h1>
  <p>モデル: <code>{MODEL_ID}</code></p>
  <h2>prompt.txt の内容</h2>
  <pre style="white-space:pre-wrap;border:1px solid #ccc;padding:8px;">{preview}</pre>
  <p><a href="/download.wav">音声を生成してダウンロード（WAV）</a></p>
</body>
</html>"""


@app.get("/download.wav")
def download_wav() -> Response:
    try:
        data = synthesize_to_wav_bytes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    name = f"gemini_tts_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.wav"
    return Response(
        content=data,
        media_type="audio/wav",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini TTS: prompt.txt を音声化")
    parser.add_argument(
        "--web",
        action="store_true",
        help="HTTP サーバを起動（ブラウザから WAV をダウンロード）",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="--web 時のバインドアドレス",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="--web 時のポート",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="CLI 実行時の出力 WAV パス（省略時はタイムスタンプ付きファイル名）",
    )
    args = parser.parse_args()

    if args.web:
        import uvicorn

        load_dotenv(BASE_DIR / ".env")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=False,
        )
        return

    try:
        run_cli(args.output)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
