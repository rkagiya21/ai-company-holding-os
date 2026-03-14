import os
import time
import requests
from loguru import logger


CLAUDE_MODEL = "claude-haiku-4-5-20251001"
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
