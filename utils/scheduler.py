"""
Daily task scheduler for PD Triglav web app
Handles automated content generation at 6 AM daily
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import atexit


def fetch_daily_news_task():
    """Scheduled task to fetch and cache daily climbing news"""
    try:
        current_app.logger.info("Starting scheduled daily news fetch...")
        from utils.daily_news import fetch_and_cache_news

        articles = fetch_and_cache_news()
        current_app.logger.info(f"Successfully cached {len(articles)} news articles")
    except Exception as e:
        current_app.logger.error(f"Error in scheduled news fetch: {e}")


def generate_historical_event_task():
    """Scheduled task to generate today's historical event if missing"""
    try:
        current_app.logger.info("!!Starting scheduled historical event generation...")
        from models.content import HistoricalEvent

        todays_event = HistoricalEvent.get_todays_event()
        if not todays_event:
            from utils.content_generation import generate_todays_historical_event

            new_event = generate_todays_historical_event()
            if new_event:
                current_app.logger.info(f"Generated historical event: {new_event.title}")
            else:
                current_app.logger.warning("Failed to generate historical event")
        else:
            current_app.logger.info(f"Historical event already exists: {todays_event.title}")
    except Exception as e:
        current_app.logger.error(f"Error in scheduled historical event generation: {e}")


def cleanup_old_data_task():
    """Weekly cleanup task to remove old cached data"""
    try:
        current_app.logger.info("Starting scheduled cleanup of old data...")
        from models.content import DailyNews

        deleted_count = DailyNews.cleanup_old_news(days_to_keep=30)
        current_app.logger.info(f"Cleaned up {deleted_count} old news entries")
    except Exception as e:
        current_app.logger.error(f"Error in scheduled cleanup: {e}")


def init_scheduler(app):
    """Initialize and start the background scheduler"""
    if app.config.get("TESTING"):
        # Don't start scheduler during testing
        return None

    scheduler = BackgroundScheduler()

    # Daily tasks at 6:00 AM
    scheduler.add_job(
        func=fetch_daily_news_task,
        trigger=CronTrigger(hour=6, minute=0),
        id="fetch_daily_news",
        name="Fetch daily mountaineering news",
        replace_existing=True,
    )

    scheduler.add_job(
        func=generate_historical_event_task,
        trigger=CronTrigger(hour=6, minute=5),  # 5 minutes after news
        id="generate_historical_event",
        name="Generate today's historical event",
        replace_existing=True,
    )

    # Weekly cleanup on Sundays at 2:00 AM
    scheduler.add_job(
        func=cleanup_old_data_task,
        trigger=CronTrigger(day_of_week=6, hour=2, minute=0),  # Sunday at 2 AM
        id="cleanup_old_data",
        name="Cleanup old cached data",
        replace_existing=True,
    )

    try:
        scheduler.start()
        app.logger.info("Background scheduler started successfully")

        # Shut down scheduler when app exits
        atexit.register(lambda: scheduler.shutdown())

        return scheduler

    except Exception as e:
        app.logger.error(f"Failed to start background scheduler: {e}")
        return None


def run_task_now(task_name):
    """Manually trigger a scheduled task (for testing/admin)"""
    tasks = {
        "news": fetch_daily_news_task,
        "historical": generate_historical_event_task,
        "cleanup": cleanup_old_data_task,
    }

    if task_name in tasks:
        try:
            tasks[task_name]()
            return True
        except Exception as e:
            current_app.logger.error(f"Error running task {task_name}: {e}")
            return False
    else:
        current_app.logger.error(f"Unknown task: {task_name}")
        return False
