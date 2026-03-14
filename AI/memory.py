"""
AI/memory.py  Phase 8
Supabaseを使った長期記憶システム
- conversations: 会話履歴（直近20件を文脈として使用）
- approvals: 承認・キャンセル履歴
- directives: 会長からの指示・設定
"""
import requests
from loguru import logger
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

MAX_HISTORY = 20


def _url(table):
    return f"{SUPABASE_URL}/rest/v1/{table}"


def save_message(user_id, role, content, mode="ceo"):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False
    try:
        res = requests.post(
            _url("conversations"),
            headers=HEADERS,
            json={"user_id": user_id, "role": role, "content": content, "mode": mode},
            timeout=5,
        )
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"[Memory] save_message失敗: {e}")
        return False


def get_history(user_id, limit=MAX_HISTORY):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return []
    try:
        res = requests.get(
            _url("conversations"),
            headers={**HEADERS, "Prefer": ""},
            params={
                "user_id": f"eq.{user_id}",
                "order": "created_at.desc",
                "limit": limit,
            },
            timeout=5,
        )
        if res.status_code == 200:
            return list(reversed(res.json()))
        return []
    except Exception as e:
        logger.warning(f"[Memory] get_history失敗: {e}")
        return []


def format_history_for_prompt(history):
    if not history:
        return ""
    lines = ["【過去の会話履歴】"]
    for h in history:
        role_label = "会長" if h["role"] == "user" else "AI CEO"
        lines.append(f"{role_label}: {h['content'][:200]}")
    return "\n".join(lines) + "\n\n"


def save_approval(user_id, action, context=""):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False
    try:
        res = requests.post(
            _url("approvals"),
            headers=HEADERS,
            json={"user_id": user_id, "action": action, "context": context},
            timeout=5,
        )
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"[Memory] save_approval失敗: {e}")
        return False


def set_directive(key, value):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False
    try:
        res = requests.post(
            _url("directives"),
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
            json={"key": key, "value": value},
            timeout=5,
        )
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"[Memory] set_directive失敗: {e}")
        return False


def get_directive(key, default=""):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return default
    try:
        res = requests.get(
            _url("directives"),
            headers={**HEADERS, "Prefer": ""},
            params={"key": f"eq.{key}", "limit": 1},
            timeout=5,
        )
        if res.status_code == 200 and res.json():
            return res.json()[0]["value"]
        return default
    except Exception as e:
        logger.warning(f"[Memory] get_directive失敗: {e}")
        return default
