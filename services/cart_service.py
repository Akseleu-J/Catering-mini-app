"""
services/cart_service.py
Business logic for cart operations and calculation engine.
"""

import math
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import CartRepository, ProductRepository
from models.models import CartItem, Product
from config import get_logger

logger = get_logger(__name__)


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.cart_repo = CartRepository(session)
        self.product_repo = ProductRepository(session)

    # ── Calculation Engine ──────────────────────────────────────────────────

    @staticmethod
    def calc_quantity_per_person(guests: int, serving_factor: int) -> int:
        """
        Per-person calculation:
        quantity = ceil(guests / serving_factor)
        e.g. 50 guests, serving_factor=10 → ceil(50/10) = 5 units
        """
        return math.ceil(guests / serving_factor)

    @staticmethod
    def calc_item_total(quantity: int, price: Decimal) -> Decimal:
        return Decimal(quantity) * price

    # ── Cart Operations ─────────────────────────────────────────────────────

    async def add_manual(self, user_id: int, product_id: int, quantity: int) -> str:
        """Add item with manual quantity."""
        product = await self.product_repo.get_by_id(product_id)
        if not product or not product.is_available:
            return "❌ Товар недоступен"
        if quantity <= 0:
            return "❌ Количество должно быть больше 0"

        await self.cart_repo.add_or_update(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            calc_mode="manual",
        )
        logger.info(f"User {user_id} added product {product_id} x{quantity} (manual)")
        return f"✅ *{product.name}* добавлен в корзину ({quantity} шт.)"

    async def add_per_person(self, user_id: int, product_id: int, guests: int) -> str:
        """Add item calculated by guest count."""
        product = await self.product_repo.get_by_id(product_id)
        if not product or not product.is_available:
            return "❌ Товар недоступен"

        quantity = self.calc_quantity_per_person(guests, product.serving_factor)
        await self.cart_repo.add_or_update(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            calc_mode="per_person",
            guests_count=guests,
        )
        logger.info(f"User {user_id} added product {product_id} x{quantity} (per_person, guests={guests})")
        return (
            f"✅ *{product.name}* добавлен в корзину\n"
            f"👥 {guests} гостей → {quantity} шт. (1 порция на {product.serving_factor} чел.)"
        )

    async def remove_item(self, user_id: int, product_id: int) -> None:
        await self.cart_repo.remove_item(user_id, product_id)

    async def clear(self, user_id: int) -> None:
        await self.cart_repo.clear_cart(user_id)

    async def get_cart_summary(self, user_id: int) -> dict:
        """Returns cart with totals."""
        items = await self.cart_repo.get_user_cart(user_id)
        total = Decimal("0")
        rows = []
        for item in items:
            subtotal = self.calc_item_total(item.quantity, item.product.price)
            total += subtotal
            rows.append({
                "product": item.product,
                "quantity": item.quantity,
                "subtotal": subtotal,
                "calc_mode": item.calc_mode,
                "guests_count": item.guests_count,
            })
        return {"items": rows, "total": total, "count": len(rows)}
