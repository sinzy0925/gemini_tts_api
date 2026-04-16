# Gemini TTS（prompt.txt → WAV）

[Gemini 3.1 Flash TTS プレビュー](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview?hl=ja) を使い、同じディレクトリの `prompt.txt` を読み上げテキストとして音声化し、WAV ファイルとして保存またはダウンロードするツールです。

## 注意事項
- 無料のGemini-api-key でも利用可能ですが、１日に１０回までしか使えません。また失敗しても、１回とカウントされますので、ご注意を。
- 無料のGemini-api-key を使う際は、個人情報などを入力しないようにご注意ください。

## 必要なもの

- Python 3.10 以上（推奨）
- [Google AI Studio などで取得した Gemini API キー](https://ai.google.dev/gemini-api/docs/api-key?hl=ja)

## セットアップ

```powershell
cd gemini_tts_api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

プロジェクト直下に `.env` を作成し、API キーを設定します（`.env.example` を参考にしてください）。

```env
GEMINI_API_KEY=あなたのAPIキー
```

任意で、プリセット音声名を変える場合:

```env
VOICE_NAME=Kore
```

## 使い方

### CLI（ローカルに WAV を保存）

```powershell
python main.py -o speech.wav
```

`-o` を省略すると、`gemini_tts_YYYYMMDD_HHMMSS.wav` のような名前でカレントに保存されます。

### Web（ブラウザから WAV をダウンロード）

ターミナル 1:

```powershell
python main.py --web
```

ブラウザで `http://127.0.0.1:8000` を開き、「音声を生成してダウンロード」のリンクから取得できます。別ホスト・ポートにする場合は `--host` / `--port` を指定してください。

## ファイル構成

| ファイル | 説明 |
|----------|------|
| `main.py` | CLI・FastAPI・TTS 処理 |
| `prompt.txt` | 読み上げる本文（UTF-8） |
| `.env` | API キーなど（Git に含めない） |
| `requirements.txt` | 依存パッケージ |

## 参考リンク

- [Gemini 3.1 Flash TTS（モデル説明）](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview?hl=ja)
- [Text-to-Speech 生成（公式ガイド）](https://ai.google.dev/gemini-api/docs/speech-generation?hl=ja)

## 注意

- プレビュー API の挙動により、まれに空の応答が返ることがあります。その場合は自動で数回リトライします。
- 長い `prompt.txt` は生成に時間がかかることがあります。
