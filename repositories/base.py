"""
repositories/base.py
Generic base repository with common CRUD operations.
All concrete repositories extend this.
"""

from typing import Generic, TypeVar, Type, Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id_: int) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def get_all(self) -> Sequence[ModelT]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()  # Get ID without committing
        return obj

    async def update_by_id(self, id_: int, **kwargs) -> None:
        await self.session.execute(
            update(self.model).where(self.model.id == id_).values(**kwargs)
        )

    async def delete_by_id(self, id_: int) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.id == id_)
        )
