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
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}]
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"Claude Error: {e}")
        return f"[Claude Error: {e}]"


def _call_gemini(system, user):
    time.sleep(1)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key: return "[Gemini Key Missing]"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": 600}
        }
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[Gemini Error: {e}]"


class AgentRouter:
    def council(self, topic):
        roles = [
            ("gemini", "You are a strategist AI. Give advice in Japanese under 200 chars."),
            ("claude", "You are a creative AI. Give advice in Japanese under 200 chars."),
            ("claude", "You are a dev AI. Give advice in Japanese under 200 chars."),
            ("claude", "You are a Kindle publisher AI. Give advice in Japanese under 200 chars."),
            ("claude", "You are a NOTE sales AI. Give advice in Japanese under 200 chars."),
            ("claude", "You are a YouTube/SNS AI. Give advice in Japanese under 200 chars.")
        ]
        icons = ["sanbo(Gemini)", "seisaku(Claude)", "kaihatsu(Claude)", "Kindle", "NOTE", "SNS"]
        results = []
        for i, (api, role_desc) in enumerate(roles):
            fn = _call_gemini if api == "gemini" else _call_claude
            op = fn(role_desc, f"Topic: {topic}")
            results.append((icons[i], op))

        ops_text = "\n".join([f"{icon}: {op}" for icon, op in results])
        final_decision = _call_claude(
            "You are AI CEO. Summarize the council and give final decision in Japanese.",
            f"Topic: {topic}\n\nCouncil:\n{ops_text}\n\nFinal decision:",
            max_tokens=800
        )

        res = "━━━━━━━━━━━━━━━\n戦略ルーム 合議結果\n"
        res += f"テーマ: {topic}\n━━━━━━━━━━━━━━━\n\n"
        for icon, op in results:
            res += f"● {icon}\n{op}\n\n"
        res += f"━━━━━━━━━━━━━━━\nAI CEO 最終合議案\n{final_decision}"
        return res
