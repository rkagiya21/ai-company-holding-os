"""AI/agents.py Phase 7"""
from __future__ import annotations
import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-3-haiku-20240307"
GEMINI_MODEL = "gemini-2.0-flash"


def _call_claude(system, user, max_tokens=600):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return "[APIキー未設定]"
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": CLAUDE_MODEL, "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}]},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[Claude] {e}")
        return f"[Claudeエラー: {e}]"


def _call_gemini(system, user):
    time.sleep(1)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return "[Gemini APIキー未設定]"
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}",
            json={"system_instruction": {"parts": [{"text": system}]}, "contents": [{"parts": [{"text": user}]}], "generationConfig": {"maxOutputTokens": 600}},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[Gemini] {e}")
        return f"[Geminiエラー: {e}]"


class StrategistAgent:
    name, icon = "参謀（Gemini）", "🔭"
    def think(self, t):
        return _call_gemini("AI会社の参謀として200字以内で意見を述べ「推奨アクション:〇〇」と明記。", f"参謀として意見を: {t}")


class CreativeAgent:
    name, icon = "制作（Claude）", "✍️"
    def think(self, t):
        return _call_claude("AI会社の制作担当として200字以内で意見を述べ「制作プラン:〇〇」と明記。", f"制作担当として意見を: {t}")


class DevAgent:
    name, icon = "開発（Claude）", "⚙️"
    def think(self, t):
        return _call_claude("AI会社の開発担当として200字以内で意見を述べ「実装方針:〇〇」と明記。", f"開発担当として意見を: {t}")


class KindleAgent:
    name, icon = "Kindle担当", "📚"
    def think(self, t):
        return _call_claude("Kindle出版専門家として200字以内で意見を述べ「出版戦略:〇〇」と明記。", f"Kindle担当として意見を: {t}")


class NoteAgent:
    name, icon = "NOTE担当", "📝"
    def think(self, t):
        return _call_claude("NOTE販売専門家として200字以内で意見を述べ「NOTE戦略:〇〇」と明記。", f"NOTE担当として意見を: {t}")


class YouTubeSNSAgent:
    name, icon = "YouTube/SNS担当", "🎬"
    def think(self, t):
        return _call_claude("YouTube・SNS専門家として200字以内で意見を述べ「拡散戦略:〇〇」と明記。", f"YouTube/SNS担当として意見を: {t}")


class CEOAgent:
    name, icon = "AI CEO", "👑"
    def synthesize(self, topic, opinions):
        txt = "\n".join(f"【{o['name']}】{o['opinion']}" for o in opinions)
        sys = "CEO として各意見を統合し最終合議案を作成。■各意見要点 ■総合判断150字 ■推奨アクション 承認要の場合→承認必要YES/NO"
        return _call_claude(sys, f"テーマ:{topic}\n\n{txt}\n\n最終合議案を:", max_tokens=1000)


class AgentRouter:
    def __init__(self):
        self.agents = [StrategistAgent(), CreativeAgent(), DevAgent(), KindleAgent(), NoteAgent(), YouTubeSNSAgent()]
        self.ceo = CEOAgent()

    def council(self, topic):
        logger.info(f"[Council] 開始: {topic[:30]}")
        opinions = []
        for a in self.agents:
            try:
                op = a.think(topic)
                opinions.append({"name": f"{a.icon} {a.name}", "opinion": op})
            except Exception as e:
                opinions.append({"name": f"{a.icon} {a.name}", "opinion": f"[エラー:{e}]"})
        final = self.ceo.synthesize(topic, opinions)
        res = "━━━━━━━━━━━━━━━\n🏛️ 戦略ルーム 合議結果\n"
        res += f"テーマ: {topic}\n━━━━━━━━━━━━━━━\n\n"
        for o in opinions:
            res += f"{o['name']}\n{o['opinion']}\n\n"
        res += f"━━━━━━━━━━━━━━━\n👑 AI CEO 最終合議案\n{final}"
        return res
