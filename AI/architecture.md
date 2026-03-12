# AI Company Holding OS — アーキテクチャ詳細

## システム全体図

```
┌─────────────────────────────────────────────────────────────┐
│  CEO（あなた）                                                │
│  ・毎朝 LINE で報告を受け取る                                  │
│  ・承認リクエストに返信するだけ                                  │
└────────────────────────┬────────────────────────────────────┘
                         │ LINE
┌────────────────────────▼────────────────────────────────────┐
│  LINE ゲートキーパー（src/line_gateway/）                      │
│  ・毎朝 9:00 朝次報告を送信                                    │
│  ・承認リクエストの送受信                                       │
│  ・コマンド解析（状況/リサーチ/ヘルプ等）                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  AI CEO（src/aiceo/）— LangGraph State Machine               │
│                                                             │
│  research → strategy → approval_gate → execute → analyze    │
│      ↑______________________________________________|        │
│                                                             │
│  ・承認不要タスク → 自動実行                                    │
│  ・承認必要タスク → LINE通知 → 人間の返信待ち                    │
└────────────────────────┬────────────────────────────────────┘
                         │ Dify REST API
┌────────────────────────▼────────────────────────────────────┐
│  Dify（実行部隊）— 各ワークフロー                               │
│  ・Kindle 生成WF（稼働中 / 11冊完成）                          │
│  ・NOTE リライトWF（Phase 3 で構築）                           │
│  ・リサーチWF（Phase 3 で構築）                                │
│  ・KAMUI改修WF（HOLD 中 — 将来API接続）                        │
└─────────────┬──────────────────┬───────────────────────────┘
              │                  │
    ┌─────────▼──────┐   ┌──────▼──────────────────────────┐
    │  Google Drive  │   │  外部API                         │
    │  Kindle原稿    │   │  ・KDP (出版 — 要承認)             │
    │  NOTE記事      │   │  ・DALL-E (カバー生成)             │
    └────────────────┘   │  ・X / Instagram / Threads       │
                         │  ・YouTube Data API              │
                         │  ・KAMUI API（将来 / HOLD中）     │
                         └─────────────────────────────────┘
```

## LangGraph State Machine 詳細

### State（AICompanyState）
```
current_task      — 現在のタスク名
topic             — リサーチ・実行対象
research_result   — リサーチ結果 (dict)
strategy          — 戦略 (dict)
requires_approval — 承認が必要か (bool)
execution_target  — 実行する Dify WF キー
execution_result  — 実行結果 (dict)
analysis          — 分析結果 (dict)
approval_status   — none / waiting / approved / rejected
pending_approvals — 承認待ちリスト
loop_count        — ループ回数（暴走防止）
```

### ノード詳細

| ノード | 処理 | LLM | Dify |
|--------|------|-----|------|
| research | 市場調査 | gpt-4o-mini | リサーチWF |
| strategy | 戦略立案・承認判定 | gpt-4o | — |
| approval_gate | LINEへ承認リクエスト送信 | — | — |
| execute | DifyWFをキック | — | 対象WF |
| analyze | 結果分析・次ループ決定 | gpt-4o-mini | — |

## 承認ゲート — 対象アクション

| アクション | 理由 |
|-----------|------|
| kdp_publish | KDP出版（本番公開） |
| note_paid_publish | NOTE有料記事公開 |
| ad_spend | 広告費発生 |
| new_business_launch | 新規事業着手 |
| kamui_db_change | KAMUI DBスキーマ変更（HOLD中） |
| external_payment | 外部への支払い |
| auth_credential_use | 認証情報使用 |

## KAMUI 保護ルール

```
⚠️ KAMUI リポジトリには一切触れない
Protected Tag: backup-2026-03-12-gacha-working
Protected Commit: 96367a3
DifyClient.run_workflow("kamui") → 自動ブロック
KAMUI_TASKS_ON_HOLD = True（settings.py）
```

## セットアップ手順

1. LINE Developers でチャンネル作成 → Webhook URL を `/webhook` に設定
2. Dify で各WF作成 → APIキーを `.env` に記入
3. Supabase でデータ収集テーブル設定
4. `docker-compose up -d` で起動
5. ngrok 等で LINE Webhook URLを公開（開発時）

## Phase ロードマップ

```
Phase 2.5 (今)  : AI CEO + LINE ゲートキーパー 実装 ✅
Phase 3 (次)    : Kindle カバー + KDP + NOTE 連鎖WF
Phase 4 (次々)  : SNS 全自動化
Phase 5         : YouTube 全自動化
Phase 6 (HOLD)  : KAMUI 残タスク 15件
Phase 7         : 完全自律経営
```
