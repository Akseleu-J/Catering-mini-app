"""scheduler/__init__.py — APScheduler configuration and job registration."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot

from .review_scheduler import send_review_requests
from config import get_logger

logger = get_logger(__name__)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and configure the async scheduler with all jobs."""
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

    # Review requests: check every hour
    scheduler.add_job(
        func=send_review_requests,
        trigger=IntervalTrigger(hours=1),
        kwargs={"bot": bot},
        id="review_requests",
        name="Send review requests after events",
        replace_existing=True,
        misfire_grace_time=300,  # Allow 5min delay tolerance
    )

    logger.info("Scheduler configured with jobs: review_requests")
    return scheduler
