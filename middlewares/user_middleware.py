"""middlewares/user_middleware.py — Auto-registers users on every update."""

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import UserRepository
from config import get_logger

logger = get_logger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Update):
            if event.message:
                user = event.message.from_user
            elif event.callback_query:
                user = event.callback_query.from_user

        if user and not user.is_bot:
            session: AsyncSession = data.get("session")
            if session:
                repo = UserRepository(session)
                db_user, created = await repo.get_or_create(
                    user_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                )
                if created:
                    logger.info(f"New user registered: {user.id} @{user.username}")
                data["db_user"] = db_user

        return await handler(event, data)
