"""
config/settings.py
全環境変数・設定値の一元管理
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o-mini" # デフォルト（戦略立案は gpt-4o）
LLM_MODEL_HEAVY = "gpt-4o"

# ── Dify ────────────────────────────────────
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")

# Dify ワークフロー App ID
DIFY_APP_IDS = {
    "kindle": "95e287a0-212e-4955-80f8-c4cd059cac97",
    "note":   "ebc36981-bbbd-4c37-9f60-4a40e2ce2b80",
    "youtube":"aa55508c-8e60-44a4-8142-d4e0d8980301",
    "sns":    "d45b7d99-70c8-45a6-b855-963894975d32",
    # KAMUI は将来用・現在 HOLD
    "kamui":  os.getenv("DIFY_KAMUI_APP_ID", ""),
}

# Dify ワークフロー APIキー（env優先、フォールバックにハードコード）
DIFY_WORKFLOWS = {
    "kindle":  os.getenv("DIFY_KINDLE_WF_KEY",  "app-HQR7HLD8bCm5V8bBdOaDMs2i"),
    "note":    os.getenv("DIFY_NOTE_WF_KEY",    "app-1yaErJPARRSnzMeDjGKyIr3h"),
    "youtube": os.getenv("DIFY_YOUTUBE_WF_KEY", "app-aayvGD8nmfqGhVT7q19zSTsm"),
    "sns":     os.getenv("DIFY_SNS_WF_KEY",     "app-54G2KrB5uRtkTS5ExRYBIRCI"),
    "research":os.getenv("DIFY_RESEARCH_WF_KEY",""),
    # KAMUI は将来用・現在 HOLD
    "kamui":   os.getenv("DIFY_KAMUI_WF_KEY",   ""),
}

# ── LINE ────────────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "") # 承認通知送信先

# ── Supabase ────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── KAMUI（保護）────────────────────────────────────
KAMUI_API_BASE_URL = os.getenv("KAMUI_API_BASE_URL", "")
KAMUI_API_KEY = os.getenv("KAMUI_API_KEY", "")
KAMUI_PROTECTED_TAG = "backup-2026-03-12-gacha-working"
KAMUI_PROTECTED_COMMIT = "96367a3"
KAMUI_TASKS_ON_HOLD = True # 全事業安定まで変更禁止

# ── Google Drive / GAS ────────────────────────────────────
GAS_ENDPOINT = os.getenv("GAS_ENDPOINT", "https://script.google.com/macros/s/AKfycbz_r5osMYpT2hk5W8vuNMmNq4R12oawPLI2gXK6hDbmodLKTbnbC7a2pP784ikz-7KkpQ/exec")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1_uEbUwp5fVZnyI6IUO7Hzu-cYIcRx1xN")

# ── DALL-E ────────────────────────────────────
DALLE_MODEL = os.getenv("DALLE_MODEL", "dall-e-3")

# ── Scheduler ────────────────────────────────────
REPORT_CRON_HOUR = int(os.getenv("REPORT_CRON_HOUR", "9"))
REPORT_CRON_MINUTE = int(os.getenv("REPORT_CRON_MINUTE", "0"))
REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "Asia/Tokyo")

# ── App ────────────────────────────────────
ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── 承認が必要なアクション（ゲートキーパー定義）────────────────────────────────────
APPROVAL_REQUIRED_ACTIONS = [
    "kdp_publish",         # KDP出版
    "note_paid_publish",   # NOTE有料公開
    "ad_spend",            # 広告出稿
    "new_business_launch", # 新規事業着手
    "kamui_db_change",     # KAMUI DBスキーマ変更
    "external_payment",    # 外部への支払い
    "auth_credential_use", # 認証情報使用
]
