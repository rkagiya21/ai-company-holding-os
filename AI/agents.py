import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL = "gemini-2.0-flash"


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


class AgentRouter:
    def council(self, topic):
        ctx = (
            "あなたはAI開発・コンテンツ販売会社の役員です。"
            "Phase 7完全自律経営を目指しています。"
            "ルール: 雑談禁止、150字以内のチャット形式で発言すること。"
        )

        # 1. 参謀（Gemini優先、失敗時はClaudeが代行）
        sys1 = f"{ctx} あなたは【経営参謀】。戦略・リスクを端的に示せ。"
        op1 = _call_gemini(sys1, topic)
        if not op1:
            op1 = _call_claude(sys1 + "（参謀代行）", topic)

        # 2. 開発事業部長（参謀の発言を受けてツッコむ）
        sys2 = f"{ctx} あなたは【開発事業部長】。参謀の意見にツッコみつつ自動化案を出せ。"
        op2 = _call_claude(sys2, f"議題:{topic}\n参謀:{op1}")

        # 3. コンテンツ事業部長
        sys3 = f"{ctx} あなたは【コンテンツ事業部長】。開発案を受けKindle/NOTE収益化の観点で発言せよ。"
        op3 = _call_claude(sys3, f"議題:{topic}\n開発:{op2}")

        # 4. SNS事業部長
        sys4 = f"{ctx} あなたは【SNS事業部長】。コンテンツ案を受けYouTube/SNS拡散策を出せ。"
        op4 = _call_claude(sys4, f"議題:{topic}\n制作:{op3}")

        # 5. AI CEO（最終決済）
        sys_ceo = f"{ctx} あなたは【AI CEO】。議論を総括し会長へYES/NOで問う最終案を出せ。"
        ceo = _call_claude(sys_ceo, f"議題:{topic}\n議論:{op1} / {op2} / {op3} / {op4}", max_tokens=800)

        res = f"🏛️ 経営会議: {topic}\n\n"
        res += f"🔭 参謀\n{op1}\n\n"
        res += f"⚙️ 開発\n{op2}\n\n"
        res += f"✍️ 制作\n{op3}\n\n"
        res += f"🎬 SNS\n{op4}\n\n"
        res += f"━━━━━━━━━━━━━━━\n👑 CEO 最終決済案\n{ceo}"
        return res
