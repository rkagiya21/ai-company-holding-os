import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"

# 会社コンテキスト＆キャラクター定義
CTX = (
    "弊社はAI開発・コンテンツ販売会社。Phase 7完全自律経営を目指す。"
    "雑談禁止。150字以内のチャット形式で発言すること。"
    "メンバー: ボブ(CEO), ジェミちゃん(参謀), テック君(開発), カリスマ(コンテンツ), 映え子さん(SNS)。"
)

# メンション（あだ名）→エージェントID マッピング
MENTION_MAP = {
    "テック": "tech",
    "ジェミ": "sanbo",
    "カリスマ": "content",
    "映え": "sns",
    "ボブ": "ceo",
    "bob": "ceo",
    "tech": "tech",
    "開発": "tech",
    "参謀": "sanbo",
    "コンテンツ": "content",
    "制作": "content",
    "sns": "sns",
    "youtube": "sns",
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


def detect_mention(text):
    """あだ名・メンションを検出してエージェントIDを返す。なければNone"""
    lower = text.lower()
    for keyword, agent_id in MENTION_MAP.items():
        if keyword.lower() in lower:
            return agent_id
    return None


class AgentRouter:

    def _gemini_sanbo(self, topic):
        sys1 = f"{CTX} あなたは【ジェミちゃん】経営参謀。戦略・リスクを端的に示せ。"
        op = _call_gemini(sys1, topic)
        if not op:
            op = _call_claude(f"{CTX} あなたは【ジェミちゃん】経営参謀（代行）。戦略を示せ。", topic)
        return ("🔭 ジェミちゃん（経営参謀）", op)

    def _claude_tech(self, topic, prev=""):
        sys2 = f"{CTX} あなたは【テック君】開発事業部長。Dify/APIでの自動化案を端的に出せ。"
        user = f"議題:{topic}" + (f"\n前の発言:{prev}" if prev else "")
        return ("⚙️ テック君（開発事業部長）", _call_claude(sys2, user))

    def _claude_content(self, topic, prev=""):
        sys3 = f"{CTX} あなたは【カリスマ】コンテンツ事業部長。Kindle/NOTE収益化の観点で発言せよ。"
        user = f"議題:{topic}" + (f"\n前の発言:{prev}" if prev else "")
        return ("✍️ カリスマ（コンテンツ事業部長）", _call_claude(sys3, user))

    def _claude_sns(self, topic, prev=""):
        sys4 = f"{CTX} あなたは【映え子さん】SNS事業部長。YouTube/SNS集客策を端的に出せ。"
        user = f"議題:{topic}" + (f"\n前の発言:{prev}" if prev else "")
        return ("🎬 映え子さん（SNS事業部長）", _call_claude(sys4, user))

    def _claude_ceo(self, topic, discussion=""):
        sys_ceo = (
            f"{CTX} あなたは【ボブ】AI CEO。議論を短く総括し会長へYES/NOで問え。"
            "わからないことを聞かれたら中学生でも分かるように噛み砕いて説明すること。"
        )
        user = f"議題:{topic}" + (f"\n議論:{discussion}" if discussion else "")
        return ("👑 ボブ（AI CEO）", _call_claude("".join(sys_ceo), user, max_tokens=500))

    def council(self, topic):
        """メンション検出 → 指名された1人だけ / なければ全員会議"""
        target = detect_mention(topic)

        # 指名モード（API1回のみ = コスト最小）
        if target == "tech":
            return [self._claude_tech(topic)]
        elif target == "sanbo":
            return [self._gemini_sanbo(topic)]
        elif target == "content":
            return [self._claude_content(topic)]
        elif target == "sns":
            return [self._claude_sns(topic)]
        elif target == "ceo":
            return [self._claude_ceo(topic)]

        # 全員会議モード（連鎖型）
        n1, op1 = self._gemini_sanbo(topic)
        n2, op2 = self._claude_tech(topic, op1)
        n3, op3 = self._claude_content(topic, op2)
        n4, op4 = self._claude_sns(topic, op3)
        all_ops = f"{op1} / {op2} / {op3} / {op4}"
        n5, op5 = self._claude_ceo(topic, all_ops)

        return [(n1, op1), (n2, op2), (n3, op3), (n4, op4), (n5, op5)]
