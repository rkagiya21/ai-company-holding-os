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
