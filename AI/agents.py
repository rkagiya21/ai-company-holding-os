import os
import time
import requests
from loguru import logger

CLAUDE_MODEL = "claude-3-haiku-20240307"
GEMINI_MODEL = "gemini-2.0-flash"


def _call_claude(system, user, max_tokens=600):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return "[APIkey not set]"
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": CLAUDE_MODEL, "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}]},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[Claude] {e}")
        return f"[Claude error: {e}]"


def _call_gemini(system, user):
    time.sleep(2)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return "[Gemini key not set]"
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}",
            json={"system_instruction": {"parts": [{"text": system}]}, "contents": [{"parts": [{"text": user}]}], "generationConfig": {"maxOutputTokens": 600}},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logger.error(f"[Gemini] {e}")
        return f"[Gemini error: {e}]"


class AgentRouter:
    def council(self, topic):
        roles = [
            ("gemini", "strategist AI. Advise in Japanese under 200 chars."),
            ("claude", "creative AI. Advise in Japanese under 200 chars."),
            ("claude", "dev AI. Advise in Japanese under 200 chars."),
            ("claude", "Kindle publisher AI. Advise in Japanese under 200 chars."),
            ("claude", "NOTE sales AI. Advise in Japanese under 200 chars."),
            ("claude", "YouTube/SNS AI. Advise in Japanese under 200 chars."),
        ]
        icons = ["sanbo(Gemini)", "seisaku(Claude)", "kaihatsu(Claude)", "Kindle", "NOTE", "SNS"]
        results = []
        for i, (api, sys_msg) in enumerate(roles):
            fn = _call_gemini if api == "gemini" else _call_claude
            try:
                op = fn(sys_msg, f"Topic: {topic}")
            except Exception as e:
                op = f"[error: {e}]"
            results.append((icons[i], op))

        ops_text = "\n".join(f"[{icon}] {op}" for icon, op in results)
        final = _call_claude(
            "You are CEO. Summarize and decide in Japanese. Say YES/NO if approval needed.",
            f"Topic: {topic}\n\n{ops_text}\n\nDecision:",
            max_tokens=1000,
        )
        out = "━━━━━━━━━━━━━━━\n戦略ルーム 合議結果\n"
        out += f"テーマ: {topic}\n━━━━━━━━━━━━━━━\n\n"
        for icon, op in results:
            out += f"{icon}\n{op}\n\n"
        out += f"━━━━━━━━━━━━━━━\nAI CEO 最終合議案\n{final}"
        return out
