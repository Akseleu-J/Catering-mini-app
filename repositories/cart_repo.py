"""repositories/cart_repo.py"""

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import CartItem, Product
from .base import BaseRepository


class CartRepository(BaseRepository[CartItem]):
    model = CartItem

    async def get_user_cart(self, user_id: int) -> list[CartItem]:
        """Get all cart items for user with product eagerly loaded."""
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.id)
        )
        return list(result.scalars().all())

    async def get_item(self, user_id: int, product_id: int) -> CartItem | None:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_or_update(
        self,
        user_id: int,
        product_id: int,
        quantity: int,
        calc_mode: str = "manual",
        guests_count: int | None = None,
    ) -> CartItem:
        item = await self.get_item(user_id, product_id)
        if item:
            item.quantity = quantity
            item.calc_mode = calc_mode
            item.guests_count = guests_count
        else:
            item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
                calc_mode=calc_mode,
                guests_count=guests_count,
            )
            self.session.add(item)
        await self.session.flush()
        return item

    async def remove_item(self, user_id: int, product_id: int) -> None:
        await self.session.execute(
            delete(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )

    async def clear_cart(self, user_id: int) -> None:
        await self.session.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )

    async def cart_count(self, user_id: int) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).where(CartItem.user_id == user_id)
        )
        return result.scalar() or 0
