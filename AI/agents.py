"""
AI/agents.py Phase 7
マルチエージェント合議システム
各エージェントが意見を出し、AI CEOが統合して最終案を提出する
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
