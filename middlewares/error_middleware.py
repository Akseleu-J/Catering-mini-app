"""middlewares/error_middleware.py — Global error handler middleware."""

import asyncio
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from config import get_logger

logger = get_logger(__name__)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)

        except TelegramForbiddenError:
            # User blocked the bot
            user_id = _extract_user_id(event)
            if user_id:
                session = data.get("session")
                if session:
                    from repositories import UserRepository
                    await UserRepository(session).mark_blocked(user_id)
                    logger.warning(f"User {user_id} blocked the bot — marked inactive")

        except TelegramRetryAfter as e:
            logger.warning(f"Rate limited. Retrying after {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            return await handler(event, data)

        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            # Try to notify user
            msg = None
            if isinstance(event, Update):
                if event.message:
                    msg = event.message
                elif event.callback_query:
                    msg = event.callback_query.message
            if msg:
                try:
                    await msg.answer("⚠️ Произошла ошибка. Попробуйте позже или напишите /start")
                except Exception:
                    pass


def _extract_user_id(event: TelegramObject) -> int | None:
    if isinstance(event, Update):
        if event.message:
            return event.message.from_user.id
        if event.callback_query:
            return event.callback_query.from_user.id
    return None
