import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"

CTX = (
    "あなたはAI開発・コンテンツ販売会社の役員です。"
    "Phase 7完全自律経営を目指しています。"
    "ルール: 雑談禁止。150字以内のチャット形式で発言すること。"
)

# 名指しキーワードと対応エージェント
AGENT_KEYWORDS = {
    "参謀": "sanbo",
    "開発": "kaihatsu",
    "制作": "seisaku",
    "コンテンツ": "seisaku",
    "sns": "sns",
    "youtube": "sns",
    "kindle": "seisaku",
    "note": "seisaku",
    "ceo": "ceo",
    "社長": "ceo",
}


def _call_claude(system, user, max_tokens=600):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key: return "[API Key Missing]"
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
        logger.error(f"Claude Error: {e}")
        return f"[Claude Error: {e}]"


def _call_gemini(system, user):
    time.sleep(3)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key: return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
        r = requests.post(
            url,
            json={"system_instruction": {"parts": [{"text": system}]}, "contents": [{"parts": [{"text": user}]}], "generationConfig": {"maxOutputTokens": 600}},
            timeout=15
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except:
        return None


def detect_target(text):
    """名指しされたエージェントを検出。なければNone（全員会議）"""
    lower = text.lower()
    for keyword, agent in AGENT_KEYWORDS.items():
        if keyword in lower:
            return agent
    return None


class AgentRouter:

    def _get_sanbo(self, topic):
        sys1 = f"{CTX} あなたは【経営参謀(Gemini)】。戦略・リスクを端的に示せ。"
        op = _call_gemini(sys1, topic)
        if not op:
            op = _call_claude(f"{CTX} あなたは【経営参謀(代行)】。戦略・リスクを端的に示せ。", topic)
        return ("🔭 経営参謀", op)

    def _get_kaihatsu(self, topic, prev=""):
        sys2 = f"{CTX} あなたは【開発事業部長】。Dify/APIでの自動化案を端的に出せ。"
        user = f"議題:{topic}" + (f"\n前の発言:{prev}" if prev else "")
        return ("⚙️ 開発事業部長", _call_claude(sys2, user))

    def _get_seisaku(self, topic, prev=""):
        sys3 = f"{CTX} あなたは【コンテンツ事業部長】。Kindle/NOTE収益化の観点で発言せよ。"
        user = f"議題:{topic}" + (f"\n前の発言:{prev}" if prev else "")
        return ("✍️ コンテンツ事業部長", _call_claude(sys3, user))

    def _get_sns(self, topic, prev=""):
        sys4 = f"{CTX} あなたは【SNS事業部長】。YouTube/SNS集客策を出せ。"
        user = f"議題:{topic}" + (f"\n前の発言:{prev}" if prev else "")
        return ("🎬 SNS事業部長", _call_claude(sys4, user))

    def _get_ceo(self, topic, all_opinions):
        sys_ceo = f"{CTX} あなたは【AI CEO】。議論を短く総括し会長へYES/NOで問え。"
        return ("👑 AI CEO", _call_claude(sys_ceo, f"議題:{topic}\n議論:{all_opinions}", max_tokens=500))

    def single(self, agent, topic):
        """名指し時：対象エージェントだけ返答"""
        if agent == "sanbo":
            name, op = self._get_sanbo(topic)
        elif agent == "kaihatsu":
            name, op = self._get_kaihatsu(topic)
        elif agent == "seisaku":
            name, op = self._get_seisaku(topic)
        elif agent == "sns":
            name, op = self._get_sns(topic)
        else:
            name, op = self._get_ceo(topic, topic)
        return [(name, op)]

    def council(self, topic):
        """全員会議モード：連鎖型ディスカッション"""
        target = detect_target(topic)
        if target:
            return self.single(target, topic)

        # 全員会議
        n1, op1 = self._get_sanbo(topic)
        n2, op2 = self._get_kaihatsu(topic, op1)
        n3, op3 = self._get_seisaku(topic, op2)
        n4, op4 = self._get_sns(topic, op3)
        all_ops = f"{op1} / {op2} / {op3} / {op4}"
        n5, op5 = self._get_ceo(topic, all_ops)

        return [(n1, op1), (n2, op2), (n3, op3), (n4, op4), (n5, op5)]
