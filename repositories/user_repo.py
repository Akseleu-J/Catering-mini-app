"""repositories/user_repo.py"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_or_create(
        self, user_id: int, username: str | None, full_name: str
    ) -> tuple[User, bool]:
        """Get existing user or create new one. Returns (user, created)."""
        user = await self.session.get(User, user_id)
        if user:
            # Update info in case it changed
            user.username = username
            user.full_name = full_name
            return user, False
        user = User(id=user_id, username=username, full_name=full_name)
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def get_all_active(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_active == True, User.is_blocked == False)
        )
        return list(result.scalars().all())

    async def mark_blocked(self, user_id: int) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(is_blocked=True, is_active=False)
        )

    async def count_active(self) -> int:
        from sqlalchemy import func, select
        result = await self.session.execute(
            select(func.count()).where(User.is_active == True)
        )
        return result.scalar() or 0
