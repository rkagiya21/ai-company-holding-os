"""
AI/agents.py Phase 7
マルチエージェント合議システム
"""
from __future__ import annotations
import os
import time
import requests
from loguru import logger


CLAUDE_MODEL = "claude-3-haiku-20240307"
GEMINI_MODEL = "gemini-2.0-flash"




def _call_claude(system: str, user: str, max_tokens: int = 600) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    logger.info(f"[Claude] key_len={len(api_key)} key_start={api_key[:12] if api_key else None}")
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
        if resp.status_code != 200:
