# AI Company OS - Gemini Agent

LINEから `AI: ○○して` と送るだけでGitHub/Supabaseを自律操作します。

## エンドポイント
- GET /health
- POST /agent (X-API-Keyヘッダー必須)
- POST /webhook/line

## LINEからの使い方
```
AI: AI/bot.pyを読んでkindleコマンドを確認して
AI: ガチャ履歴テーブルを確認して
```

## Renderデプロイ
- Start Command: `gunicorn main:app`
- 環境変数: .env.example参照

## 注意
- KAMUI(backup-2026-03-12-gacha-working)は絶対に触れない
- Supabase変更前は必ずSELECTで確認
