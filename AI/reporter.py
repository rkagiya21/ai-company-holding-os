"""
src/line_gateway/reporter.py
毎朝 9:00 全事業レポートを生成して LINE に送信する
"""
from __future__ import annotations
from datetime import datetime
import pytz
from loguru import logger
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    PushMessageRequest, TextMessage,
)

from config.settings import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID, REPORT_TIMEZONE
from config.prompts import MORNING_REPORT_TEMPLATE


class MorningReporter:
    """朝次報告の生成と送信"""

    def __init__(self):
        config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        self._api_client = ApiClient(config)
        self._messaging = MessagingApi(self._api_client)

    def collect_metrics(self) -> dict:
        """
        Supabase / Dify から各事業の収益・進捗データを収集する。
        APIキー未設定時はモックデータを返す。
        """
        try:
            from supabase import create_client
            from config.settings import SUPABASE_URL, SUPABASE_KEY

            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError("Supabase未設定")

            db = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Kindle 収益
            kindle = db.table("kindle_books").select("*").execute()
            # NOTE 収益（将来実装）
            # SNS フォロワー（将来実装）

            return {
                "kindle_books": len(kindle.data),
                "kindle_revenue": 0,  # KDP API接続後に実装
                "note_articles": 0,
                "note_revenue": 0,
                "kamui_status": "HOLD（保護中）",
                "pending_approvals": 0,
            }
        except Exception as e:
            logger.warning(f"[Reporter] Supabase未接続: {e} — モックデータ使用")
            return {
                "kindle_books": 11,
                "kindle_revenue": 0,
                "note_articles": 0,
                "note_revenue": 0,
                "kamui_status": "HOLD（保護中）",
                "pending_approvals": 0,
            }

    def build_report(self) -> str:
        """朝次レポートテキストを生成する"""
        tz = pytz.timezone(REPORT_TIMEZONE)
        now = datetime.now(tz)
        metrics = self.collect_metrics()

        revenue_summary = (
            f"📚 Kindle: {metrics['kindle_books']}冊公開 / ¥{metrics['kindle_revenue']:,}\n"
            f"📝 NOTE: {metrics['note_articles']}記事 / ¥{metrics['note_revenue']:,}\n"
            f"🎰 KAMUI: {metrics['kamui_status']}"
        )

        completed_tasks = "（自動収集機能実装後に表示）"
        alerts = "現在アラートなし ✅" if metrics["pending_approvals"] == 0 else \
                 f"⚠️ 承認待ちタスク: {metrics['pending_approvals']}件"
        today_plans = "Kindle拡張WF / NOTE記事WF 構築"
        pending_approvals = "なし" if metrics["pending_approvals"] == 0 else \
                            f"{metrics['pending_approvals']}件あり — 確認してください"

        return MORNING_REPORT_TEMPLATE.format(
            date=now.strftime("%Y年%m月%d日"),
            time=now.strftime("%H:%M"),
            revenue_summary=revenue_summary,
            completed_tasks=completed_tasks,
            alerts=alerts,
            today_plans=today_plans,
            pending_approvals=pending_approvals,
        )

    def send(self) -> None:
        """LINE へレポートを送信する"""
        report_text = self.build_report()

        if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
            logger.warning("[Reporter] LINE未設定 — コンソール出力")
            print(report_text)
            return

        try:
            self._messaging.push_message(
                PushMessageRequest(
                    to=LINE_USER_ID,
                    messages=[TextMessage(type="text", text=report_text[:2000])],
                )
            )
            logger.success("[Reporter] 朝次報告送信完了")
        except Exception as e:
            logger.error(f"[Reporter] 送信エラー: {e}")
            raise
