"""
AI/scheduler.py
毎朝 9:00（JST）に全事業報告を LINE へ送信するスケジューラ
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import pytz

from settings import REPORT_CRON_HOUR, REPORT_CRON_MINUTE, REPORT_TIMEZONE
from reporter import MorningReporter


def run_morning_report():
    """毎朝 9:00 に実行される朝次報告ジョブ"""
    logger.info("[Scheduler] 朝次報告 開始")
    try:
        reporter = MorningReporter()
        reporter.send()
        logger.success("[Scheduler] 朝次報告 送信完了")
    except Exception as e:
        logger.error(f"[Scheduler] 朝次報告 エラー: {e}")


def start_scheduler():
    """スケジューラを起動する（ブロッキング）"""
    tz = pytz.timezone(REPORT_TIMEZONE)
    scheduler = BlockingScheduler(timezone=tz)

    # 毎朝 9:00 JST
    scheduler.add_job(
        run_morning_report,
        trigger=CronTrigger(
            hour=REPORT_CRON_HOUR,
            minute=REPORT_CRON_MINUTE,
            timezone=tz,
        ),
        id="morning_report",
        name="毎朝報告",
        replace_existing=True,
    )

    logger.info(
        f"[Scheduler] 起動 — 毎日 {REPORT_CRON_HOUR:02d}:{REPORT_CRON_MINUTE:02d} {REPORT_TIMEZONE}"
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("[Scheduler] 停止")
        scheduler.shutdown()


if __name__ == "__main__":
    start_scheduler()
