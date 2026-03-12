"""
config/prompts.py
AI CEO が使用するプロンプト集
"""

# ── リサーチノード ────────────────────────────────────
RESEARCH_PROMPT = """
あなたは自律経営AIのリサーチ担当です。
以下のテーマについて市場調査を行い、JSON形式で結果を返してください。

テーマ: {topic}

必ず以下の項目を含めてください:
- market_size: 市場規模（推定）
- competitors: 主要競合3〜5社
- trends: 現在のトレンド3つ
- opportunities: 参入機会2〜3つ
- risks: リスク2〜3つ
- recommended_channels: 推奨集客チャネル
- estimated_monthly_revenue: 月商目安（低・中・高）
- time_to_launch: 立ち上げ期間目安

JSON のみ返答してください（```は不要）。
"""

# ── 戦略立案ノード ────────────────────────────────────
STRATEGY_PROMPT = """
あなたは自律経営AIの戦略担当です。
以下のリサーチ結果をもとに、具体的な実行戦略を立案してください。

リサーチ結果:
{research_result}

現在稼働中の事業:
- Kindle自動生成（11冊完成）
- Dify WF（Kindle/NOTE/リサーチ）

戦略は以下を含めてください:
1. 優先アクション（3ステップ）
2. 必要リソース（ツール・API・コスト）
3. KPI（1ヶ月・3ヶ月・6ヶ月）
4. Dify WFで自動化できる部分
5. 人間の承認が必要なポイント
6. リスクヘッジ策

JSON形式で返答してください。
requires_approval フィールドに承認が必要かどうかを boolean で含めること。
"""

# ── 結果分析ノード ────────────────────────────────────
ANALYSIS_PROMPT = """
あなたは自律経営AIの分析担当です。
以下の実行結果を分析し、次のアクションを提案してください。

実行したWF: {workflow_name}
実行結果: {result}
期待していた結果: {expected}

分析結果を JSON で返してください:
- success: boolean
- achievement_rate: 達成率（0-100）
- issues: 発生した問題
- next_actions: 次に取るべきアクション（優先度付き）
- requires_human_review: 人間のレビューが必要か boolean
"""

# ── LINE 朝次報告 ────────────────────────────────────
MORNING_REPORT_TEMPLATE = """
🌅 AI Company OS — 朝次報告
━━━━━━━━━━━━━━━━━━━━
📅 {date} {time} JST

📊 【事業収益サマリー】
{revenue_summary}

✅ 【昨日の完了タスク】
{completed_tasks}

⚠️ 【問題・アラート】
{alerts}

🔜 【本日の実行予定】
{today_plans}

🔐 【承認待ちタスク】
{pending_approvals}

━━━━━━━━━━━━━━━━━━━━
承認が必要なタスクは「承認」と返信してください。
"""

# ── LINE 承認リクエスト ────────────────────────────────────
APPROVAL_REQUEST_TEMPLATE = """
🔐 【承認リクエスト】

アクション: {action_name}
内容: {description}
理由: {reason}

{details}

━━━━━━━━━━━━
✅ 実行する → 「承認」と返信
❌ キャンセル → 「キャンセル」と返信
⏸ 保留 → 「保留」と返信
"""

# ── Kindle カバー生成プロンプト ────────────────────────────────────
KINDLE_COVER_PROMPT = """
Create a professional Japanese e-book cover design for:

Title: {title}
Genre: {genre}
Target: {target}

Style requirements:
- Clean, modern, professional
- Japanese book market aesthetics
- High contrast for thumbnail visibility
- Include space for title text overlay
- No text in the image (title will be added separately)
- 1600x2560 pixels ratio

Theme: {theme_description}
"""
