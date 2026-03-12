"""
config/settings.py
全環境変数・設定値の一元管理
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o-mini"  # デフォルト（戦略立案は gpt-4o）
LLM_MODEL_HEAVY = "gpt-4o"

# ── Dify ────────────────────────────────────
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_WORKFLOWS = {
    "kindle":   os.getenv("DIFY_KINDLE_WF_KEY", ""),
    "note":     os.getenv("DIFY_NOTE_WF_KEY", ""),
    "research": os.getenv("DIFY_RESEARCH_WF_KEY", ""),
    # KAMUI は将来用・現在 HOLD
    "kamui":    os.getenv("DIFY_KAMUI_WF_KEY", ""),
}

# ── LINE ────────────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")  # 承認通知送信先

# ── Supabase ────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── KAMUI（保護）────────────────────────────────────
KAMUI_API_BASE_URL = os.getenv("KAMUI_API_BASE_URL", "")
KAMUI_API_KEY = os.getenv("KAMUI_API_KEY", "")
KAMUI_PROTECTED_TAG = "backup-2026-03-12-gacha-working"
KAMUI_PROTECTED_COMMIT = "96367a3"
KAMUI_TASKS_ON_HOLD = True  # 全事業安定まで変更禁止

# ── Google Drive / GAS ────────────────────────────────────
GAS_ENDPOINT = os.getenv("GAS_ENDPOINT", "")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

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
    "kdp_publish",          # KDP出版
    "note_paid_publish",    # NOTE有料公開
    "ad_spend",             # 広告出稿
    "new_business_launch",  # 新規事業着手
    "kamui_db_change",      # KAMUI DBスキーマ変更
    "external_payment",     # 外部への支払い
    "auth_credential_use",  # 認証情報使用
]
