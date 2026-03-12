# 🤖 AI Company Holding OS
> **Autonomous Business Architecture — LangGraph × Dify × LINE**

## 概要

LangGraph を「脳（指揮官）」、Dify を「筋肉（実行部隊）」とする自律経営エンジン。  
毎朝 9:00 に全事業の収益・進捗を LINE へ報告し、重要判断は必ず人間の承認を待つ。

```
CEO（あなた）
  └── LINE ゲートキーパー（承認 / 報告）
        └── AI CEO（LangGraph 思考ループ）
              ├── Research Node      — Web・市場調査
              ├── Strategy Node      — 戦略立案・ROI試算
              ├── Approval Gate      — 承認要否判定 → LINE通知
              ├── Execute Node       — Dify API キック
              └── Analyze Node       — 結果分析 → 次ループ
```

## リポジトリ構成

```
ai-company-holding-os/
├── src/
│   ├── aiceo/              # LangGraph 思考ループ（脳）
│   │   ├── graph.py        # メイングラフ定義
│   │   ├── nodes.py        # 各ノード実装
│   │   ├── state.py        # 状態管理
│   │   └── scheduler.py    # 毎朝9:00 スケジューラ
│   ├── dify_connector/     # Dify API 連携（筋肉）
│   │   ├── client.py       # Dify REST クライアント
│   │   └── workflows.py    # 各WF定義（Kindle/NOTE/リサーチ）
│   ├── line_gateway/       # LINE ゲートキーパー
│   │   ├── bot.py          # LINE Bot サーバ（Flask）
│   │   ├── approval.py     # 承認フロー管理
│   │   └── reporter.py     # 朝次レポート生成・送信
│   └── workflows/          # 複合ワークフロー
│       ├── kindle_chain.py # Kindle → カバー → KDP → NOTE → SNS
│       └── research.py     # 新規事業リサーチWF
├── config/
│   ├── settings.py         # 環境変数・設定
│   └── prompts.py          # LLMプロンプト集
├── tests/
│   └── test_*.py
├── docs/
│   └── architecture.md
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

## 保護ルール（KAMUI）

- 既存 KAMUI リポジトリには **一切触れない**
- `backup-2026-03-12-gacha-working` タグを基準 API として利用
- KAMUI 残タスク 15 件は他事業が安定稼働するまで **HOLD**

## Phase 優先順位

| Phase | 内容 | 状態 |
|-------|------|------|
| 2.5 | AI CEO + LINE ゲートキーパー | ▶ 実装中 |
| 3 | Kindle カバー自動生成 + KDP + NOTE | 🔜 NEXT |
| 4 | SNS 全自動化（X / IG / Threads） | ⏳ |
| 5 | YouTube 全自動化 | ⏳ |
| 6 | KAMUI 残タスク（HOLD） | ⏸ |

## クイックスタート

```bash
cp .env.example .env
# .env に各 API キーを設定

pip install -r requirements.txt

# AI CEO 起動（スケジューラ含む）
python -m src.aiceo.scheduler

# LINE Bot 起動
python -m src.line_gateway.bot
```
