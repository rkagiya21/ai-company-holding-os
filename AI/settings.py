"""
config/settings.py
全環境変数・設定値の一元管理
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o-mini"
LLM_MODEL_HEAVY = "gpt-4o"

DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_APP_IDS = {
    "kindle": "95e287a0-212e-4955-80f8-c4cd059cac97",
    "note":   "ebc36981-bbbd-4c37-9f60-4a40e2ce2b80",
    "youtube":"aa55508c-8e60-44a4-8142-d4e0d8980301",
    "sns":    "d45b7d99-70c8-45a6-b855-963894975d32",
    "kamui":  os.getenv("DIFY_KAMUI_APP_ID", ""),
}
DIFY_WORKFLOWS = {
    "kindle":  os.getenv("DIFY_KINDLE_WF_KEY",  "app-HQR7HLD8bCm5V8bBdOaDMs2i"),
    "note":    os.getenv("DIFY_NOTE_WF_KEY",    "app-1yaErJPARRSnzMeDjGKyIr3h"),
    "youtube": os.getenv("DIFY_YOUTUBE_WF_KEY", "app-aayvGD8nmfqGhVT7q19zSTsm"),
    "sns":     os.getenv("DIFY_SNS_WF_KEY",     "app-54G2KrB5uRtkTS5ExRYBIRCI"),
    "research":os.getenv("DIFY_RESEARCH_WF_KEY",""),
    "kamui":   os.getenv("DIFY_KAMUI_WF_KEY",   ""),
}

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

# Phase 8: AI Company OS専用Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

KAMUI_API_BASE_URL = os.getenv("KAMUI_API_BASE_URL", "")
KAMUI_API_KEY = os.getenv("KAMUI_API_KEY", "")
KAMUI_PROTECTED_TAG = "backup-2026-03-12-gacha-working"
KAMUI_PROTECTED_COMMIT = "96367a3"
KAMUI_TASKS_ON_HOLD = True

GAS_ENDPOINT = os.getenv("GAS_ENDPOINT", "https://script.google.com/macros/s/AKfycbz_r5osMYpT2hk5W8vuNMmNq4R12oawPLI2gXK6hDbmodLKTbnbC7a2pP784ikz-7KkpQ/exec")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1_uEbUwp5fVZnyI6IUO7Hzu-cYIcRx1xN")

REPORT_CRON_HOUR = int(os.getenv("REPORT_CRON_HOUR", "9"))
REPORT_CRON_MINUTE = int(os.getenv("REPORT_CRON_MINUTE", "0"))
REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "Asia/Tokyo")

ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

APPROVAL_REQUIRED_ACTIONS = [
    "kdp_publish", "note_paid_publish", "ad_spend",
    "new_business_launch", "kamui_db_change",
    "external_payment", "auth_credential_use",
]
