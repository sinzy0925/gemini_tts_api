# Gemini TTS（prompt.txt → WAV）

[Gemini 3.1 Flash TTS プレビュー](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview?hl=ja) を使い、同じディレクトリの `prompt.txt` を読み上げテキストとして音声化し、WAV ファイルとして保存またはダウンロードするツールです。

## 注意事項

- 無料の Gemini API キーでも利用できますが、**モデルごとに 1 日のリクエスト上限**があります（失敗したリクエストもカウントされることがあります）。枠や料金は [レート制限](https://ai.google.dev/gemini-api/docs/rate-limits?hl=ja) を参照してください。
gemini-3.1-flash-tts-previewの場合は、１日の制限は１０回です。（厳しい！）
- 無料利用時は、**個人情報や機密情報を `prompt.txt` に含めない**ようにしてください。
- プレビュー API の挙動により、**まれに空の応答**が返ることがあります。自動で最大数回リトライします（リトライ間隔は `TTS_RETRY_DELAY_SEC` で調整可能、既定は 61 秒）。
- **長い `prompt.txt`** は生成に時間がかかることがあります。

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

## 環境変数（`.env`）

リポジトリの `.env.example` をコピーして `.env` を作成し、値を設定します。

```powershell
copy .env.example .env
```

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GEMINI_API_KEY` | はい | Gemini API キー。未設定時は `GOOGLE_API_KEY` があればそちらを利用します。 |
| `TTS_RETRY_DELAY_SEC` | いいえ | リトライ前に待つ秒数。**既定は `61`**。 |
| `VOICE_NAME` | いいえ | プリセット音声名。**既定は `Kore`**。[音声・Text-to-Speech ガイド](https://ai.google.dev/gemini-api/docs/speech-generation?hl=ja) の Voice を参照。 |

`.env` の記述例（`.env.example` と同じ構成）:

```env
GEMINI_API_KEY=your-api-key-here

TTS_RETRY_DELAY_SEC=61

# VOICE_NAME=Kore
```

## 使い方

### CLI（ローカルに WAV を保存）

```powershell
python main.py -o speech.wav
```

`-o` を省略すると、`gemini_tts_YYYYMMDD_HHMMSS.wav` のような名前でカレントに保存されます。

ログを詳しく出す場合は `-v`、抑える場合は `-q` を付けます。

### Web（ブラウザから WAV をダウンロード）

```powershell
python main.py --web
```

ブラウザで `http://127.0.0.1:8000` を開き、「音声を生成してダウンロード」のリンクから取得できます。別ホスト・ポートにする場合は `--host` / `--port` を指定してください。

## ファイル構成

| ファイル | 説明 |
|----------|------|
| `main.py` | CLI・FastAPI・TTS 処理 |
| `prompt.txt` | 読み上げる本文（UTF-8） |
| `.env.example` | 環境変数のテンプレート |
| `.env` | 実際のキー・設定（Git に含めない） |
| `requirements.txt` | 依存パッケージ |

## 参考リンク

- [Gemini 3.1 Flash TTS（モデル説明）](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview?hl=ja)
- [Text-to-Speech 生成（公式ガイド）](https://ai.google.dev/gemini-api/docs/speech-generation?hl=ja)
