"""
AI/agents.py Phase 7
マルチエージェント合議システム
"""
from __future__ import annotations
import os
import requests
from loguru import logger

CLAUDE_MODEL = "claude-sonnet-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"


def _call_claude(system: str, user: str, max_tokens: int = 600) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return "[ANTHROPIC_API_KEY未設定]"
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[Claude API] {e}")
        return f"[Claudeエラー: {e}]"


def _call_gemini(system: str, user: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "[GEMINI_API_KEY未設定]"
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent?key={api_key}"
        )
        resp = requests.post(
            url,
            json={
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": 600},
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[Gemini API] {e}")
        return f"[Geminiエラー: {e}]"


class StrategistAgent:
    name = "参謀（Gemini）"
    icon = "🔭"

    def think(self, topic: str) -> str:
        system = (
            "あなたはAI会社の参謀AIです。市場トレンド・競合分析・収益予測が専門です。"
            "200字以内で意見を述べ、最後に「推奨アクション: 〇〇」と明記してください。"
        )
        return _call_gemini(system, f"参謀として意見を述べてください: {topic}")


class CreativeAgent:
    name = "制作（Claude）"
    icon = "✍️"

    def think(self, topic: str) -> str:
        system = (
            "あなたはAI会社の制作担当AIです。Kindle・NOTE・YouTube・SNSのコンテンツ制作が専門です。"
            "200字以内で具体的な制作プランを提案し、最後に「制作プラン: 〇〇」と明記してください。"
        )
        return _call_claude(system, f"制作担当として意見を述べてください: {topic}")


class DevAgent:
    name = "開発（Claude）"
    icon = "⚙️"

    def think(self, topic: str) -> str:
        system = (
            "あなたはAI会社の開発担当AIです。Webシステム・API連携・既存システム改修が専門です。"
            "200字以内で技術的実現可否と方針を述べ、最後に「実装方針: 〇〇」と明記してください。"
        )
        return _call_claude(system, f"開発担当として意見を述べてください: {topic}")


class KindleAgent:
    name = "Kindle担当"
    icon = "📚"

    def think(self, topic: str) -> str:
        system = (
            "あなたはKindle電子書籍出版の専門AIです。KDPカテゴリ戦略・タイトル・構成・価格設定が専門です。"
            "200字以内で出版戦略を提案し、最後に「出版戦略: 〇〇」と明記してください。"
        )
        return _call_claude(system, f"Kindle担当として意見を述べてください: {topic}")


class NoteAgent:
    name = "NOTE担当"
    icon = "📝"

    def think(self, topic: str) -> str:
        system = (
            "あなたはNOTE記事販売の専門AIです。有料記事戦略・NOTEアルゴリズム・フォロワー獲得が専門です。"
            "200字以内でNOTE展開戦略を提案し、最後に「NOTE戦略: 〇〇」と明記してください。"
        )
        return _call_claude(system, f"NOTE担当として意見を述べてください: {topic}")


class YouTubeSNSAgent:
    name = "YouTube/SNS担当"
    icon = "🎬"

    def think(self, topic: str) -> str:
        system = (
            "あなたはYouTube・SNS（X/Instagram）の専門AIです。バズるコンテンツ・拡散・SEOが専門です。"
            "200字以内でYouTube/SNS展開戦略を提案し、最後に「拡散戦略: 〇〇」と明記してください。"
        )
        return _call_claude(system, f"YouTube/SNS担当として意見を述べてください: {topic}")


class CEOAgent:
    name = "AI CEO"
    icon = "👑"

    def synthesize(self, topic: str, opinions: list[dict]) -> str:
        opinions_text = "\n".join(
            f"【{o['name']}】{o['opinion']}" for o in opinions
        )
        system = (
            "あなたはAI会社のCEOです。各エージェントの意見を統合して会長への最終合議案を作成します。\n"
            "形式:\n"
            "■ 各意見の要点（箇条書き）\n"
            "■ 総合判断（150字以内）\n"
            "■ 推奨アクション（具体的な次の1手）\n"
            "■ 承認が必要な場合は「→ 承認が必要です。YES/NOで返答ください」と明記"
        )
        user = (
            f"テーマ: {topic}\n\n"
            f"各エージェントの意見:\n{opinions_text}\n\n"
            "上記を統合して最終合議案を作成してください。"
        )
        return _call_claude(system, user, max_tokens=1000)


class AgentRouter:
    def __init__(self):
        self.agents = [
            StrategistAgent(),
            CreativeAgent(),
            DevAgent(),
            KindleAgent(),
            NoteAgent(),
            YouTubeSNSAgent(),
        ]
        self.ceo = CEOAgent()

    def council(self, topic: str) -> str:
        logger.info(f"[AgentRouter] 合議開始: {topic[:30]}")
        opinions = []
        for agent in self.agents:
            try:
                opinion = agent.think(topic)
                opinions.append({"name": f"{agent.icon} {agent.name}", "opinion": opinion})
                logger.info(f"[{agent.name}] 意見取得完了")
            except Exception as e:
                opinions.append({"name": f"{agent.icon} {agent.name}", "opinion": f"[エラー: {e}]"})

        final = self.ceo.synthesize(topic, opinions)

        result = "━━━━━━━━━━━━━━━\n"
        result += "🏛️ 戦略ルーム 合議結果\n"
        result += f"テーマ: {topic}\n"
        result += "━━━━━━━━━━━━━━━\n\n"
        for o in opinions:
            result += f"{o['name']}\n{o['opinion']}\n\n"
        result += "━━━━━━━━━━━━━━━\n"
        result += f"👑 AI CEO 最終合議案\n{final}"
        return result
