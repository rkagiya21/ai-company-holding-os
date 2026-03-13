"""
AI/scheduler.py - GitHub Actions entrypoint
BlockingScheduler を使わず reporter を直接1回呼んで終了する。
cron は daily.yml 側で管理。
"""
from loguru import logger
from reporter import MorningReporter


def main():
    logger.info("[Scheduler] 朝次報告 開始")
    try:
        reporter = MorningReporter()
        reporter.send()
        logger.success("[Scheduler] 朝次報告 完了")
    except Exception as e:
        logger.error(f"[Scheduler] エラー: {e}")
        raise


if __name__ == "__main__":
    main()
