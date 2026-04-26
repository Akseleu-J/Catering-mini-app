"""
scheduler/review_scheduler.py
APScheduler task: sends review requests 1 day after event_date.
Runs every hour. Uses review_sent flag to prevent duplicates.
"""

from datetime import datetime
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import AsyncSessionLocal
from repositories.order_repo import OrderRepository, ReviewRepository
from keyboards.user_kb import review_rating_kb
from config import get_logger

logger = get_logger(__name__)


async def send_review_requests(bot: Bot) -> None:
    """
    Called every hour by APScheduler.
    Finds completed orders past their event_date + 1 day
    that don't have a review sent yet, and sends review request.
    """
    async with AsyncSessionLocal() as session:
        try:
            order_repo = OrderRepository(session)
            review_repo = ReviewRepository(session)

            orders = await order_repo.get_for_review_check()

            for order in orders:
                try:
                    if not order.user_id:
                        continue

                    # Create review record (marks as sent)
                    existing = await review_repo.get_by_order(order.id)
                    if existing and existing.review_sent:
                        continue

                    review = await review_repo.create_for_order(order.id, order.user_id)

                    await bot.send_message(
                        chat_id=order.user_id,
                        text=(
                            f"🌟 *Как прошло ваше мероприятие?*\n\n"
                            f"Заказ *#{order.order_uid}* от {order.event_date.strftime('%d.%m.%Y')}.\n\n"
                            f"Оцените наш сервис — это займёт всего 10 секунд! 🙏"
                        ),
                        parse_mode="Markdown",
                        reply_markup=review_rating_kb(order.id),
                    )

                    await session.commit()
                    logger.info(f"Review request sent for order #{order.order_uid} to user {order.user_id}")

                except Exception as e:
                    logger.error(f"Failed to send review for order {order.id}: {e}")
                    await session.rollback()

        except Exception as e:
            logger.error(f"Review scheduler error: {e}")
