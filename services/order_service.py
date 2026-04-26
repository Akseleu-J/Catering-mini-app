"""
services/order_service.py
Order creation, validation, checkout logic.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import OrderRepository, CartRepository, ProductRepository, ReviewRepository
from models.models import Order, OrderStatus
from config import settings, get_logger
from utils.whatsapp import build_whatsapp_link

logger = get_logger(__name__)


class OrderValidationError(Exception):
    pass


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.order_repo = OrderRepository(session)
        self.cart_repo = CartRepository(session)
        self.product_repo = ProductRepository(session)
        self.review_repo = ReviewRepository(session)

    def validate_event_datetime(self, event_dt: datetime) -> None:
        """Raises OrderValidationError if event is too soon or in the past."""
        now = datetime.utcnow()
        if event_dt <= now:
            raise OrderValidationError("❌ Дата мероприятия уже прошла.")
        lead = event_dt - now
        if lead < timedelta(hours=settings.min_lead_hours):
            raise OrderValidationError(
                f"❌ Заказ нужно оформить минимум за {settings.min_lead_hours} часов до мероприятия."
            )

    async def checkout(
        self,
        user_id: int,
        client_name: str,
        event_date: datetime,
        location: str,
    ) -> Order:
        """Full checkout: validate → create order → clear cart → return order."""
        self.validate_event_datetime(event_date)

        # Load cart
        cart_items = await self.cart_repo.get_user_cart(user_id)
        if not cart_items:
            raise OrderValidationError("❌ Корзина пуста.")

        # Calculate total
        items_data = []
        total = Decimal("0")
        for ci in cart_items:
            subtotal = Decimal(ci.quantity) * ci.product.price
            total += subtotal
            items_data.append({"product": ci.product, "quantity": ci.quantity})

        # Create order
        order = await self.order_repo.create_with_items(
            user_id=user_id,
            client_name=client_name,
            event_date=event_date,
            location=location,
            items=items_data,
            total_price=float(total),
        )

        # Clear cart
        await self.cart_repo.clear_cart(user_id)

        logger.info(f"Order #{order.order_uid} created for user {user_id}, total={total}")
        return order

    async def get_whatsapp_link(self, order: Order) -> str:
        """Generate WhatsApp link with encoded order summary."""
        full_order = await self.order_repo.get_with_items(order.id)
        return build_whatsapp_link(full_order, settings.admin_whatsapp)

    async def get_user_orders(self, user_id: int) -> list[Order]:
        return await self.order_repo.get_user_orders(user_id)

    async def repeat_order(self, user_id: int, order_id: int) -> str:
        """Copy order items into user's cart (repeat order feature)."""
        order = await self.order_repo.get_with_items(order_id)
        if not order or order.user_id != user_id:
            return "❌ Заказ не найден."

        count = 0
        for oi in order.items:
            if oi.product_id:
                product = await self.product_repo.get_by_id(oi.product_id)
                if product and product.is_available:
                    await self.cart_repo.add_or_update(
                        user_id=user_id,
                        product_id=oi.product_id,
                        quantity=oi.quantity,
                    )
                    count += 1

        if count == 0:
            return "❌ Товары из этого заказа недоступны."
        return f"✅ {count} позиций добавлено в корзину из прошлого заказа."

    async def mark_done(self, order_id: int) -> None:
        await self.order_repo.update_by_id(order_id, status=OrderStatus.DONE)

    async def mark_confirmed(self, order_id: int) -> None:
        await self.order_repo.update_by_id(order_id, status=OrderStatus.CONFIRMED)
