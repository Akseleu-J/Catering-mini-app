"""
bot.py — Main entry point.
Initialises bot, dispatcher, middlewares, routers, scheduler.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings, setup_logging, get_logger
from models import create_all_tables
from middlewares import DbSessionMiddleware, UserMiddleware, ErrorMiddleware
from scheduler import create_scheduler

# Import all routers
from handlers import common, menu, cart, checkout, orders, ai_handler, review, admin, broadcast

setup_logging()
logger = get_logger(__name__)

BOT_COMMANDS = [
    BotCommand(command="start",  description="🏠 Главная"),
    BotCommand(command="admin",  description="⚙️ Панель администратора"),
]


async def on_startup(bot: Bot) -> None:
    await bot.set_my_commands(BOT_COMMANDS)
    await create_all_tables()
    logger.info("Database tables verified ✅")
    try:
        await bot.send_message(settings.admin_id, "🟢 *Бот запущен!*\n/admin", parse_mode="Markdown")
    except Exception:
        pass
    logger.info("Bot started ✅")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot shutting down...")


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp  = Dispatcher(storage=MemoryStorage())

    # ── Middlewares (order matters) ───────────────────────────────────────────
    dp.update.outer_middleware(ErrorMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserMiddleware())

    # ── Routers (admin first — higher priority) ───────────────────────────────
    dp.include_router(admin.router)
    dp.include_router(broadcast.router)
    dp.include_router(common.router)
    dp.include_router(menu.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(orders.router)
    dp.include_router(review.router)
    dp.include_router(ai_handler.router)  # Last: catches all text

    # ── Lifecycle hooks ───────────────────────────────────────────────────────
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # ── Scheduler ─────────────────────────────────────────────────────────────
    scheduler = create_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started ✅")

    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
