"""repositories/product_repo.py"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Category, Product
from .base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def get_active(self) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.sort_order, Category.id)
        )
        return list(result.scalars().all())

    async def get_all_with_counts(self) -> list[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.sort_order, Category.id)
        )
        return list(result.scalars().all())


class ProductRepository(BaseRepository[Product]):
    model = Product

    async def get_by_category(
        self, category_id: int, available_only: bool = True, offset: int = 0, limit: int = 5
    ) -> list[Product]:
        q = select(Product).where(Product.category_id == category_id)
        if available_only:
            q = q.where(Product.is_available == True)
        q = q.order_by(Product.id).offset(offset).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count_by_category(self, category_id: int, available_only: bool = True) -> int:
        from sqlalchemy import func
        q = select(func.count()).where(Product.category_id == category_id)
        if available_only:
            q = q.where(Product.is_available == True)
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def toggle_availability(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if product:
            product.is_available = not product.is_available
            await self.session.flush()
            return product.is_available
        return False
