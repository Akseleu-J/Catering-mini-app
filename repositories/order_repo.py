"""repositories/order_repo.py"""

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Order, OrderItem, Review, OrderStatus
from .base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def create_with_items(
        self,
        user_id: int,
        client_name: str,
        event_date: datetime,
        location: str,
        items: list[dict],  # [{"product": Product, "quantity": int}]
        total_price: float,
    ) -> Order:
        import uuid
        order = Order(
            order_uid=uuid.uuid4().hex[:8].upper(),
            user_id=user_id,
            client_name=client_name,
            event_date=event_date,
            location=location,
            total_price=total_price,
        )
        self.session.add(order)
        await self.session.flush()  # Get order.id

        for item_data in items:
            product = item_data["product"]
            oi = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=item_data["quantity"],
            )
            self.session.add(oi)

        await self.session.flush()
        return order

    async def get_with_items(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    async def get_user_orders(self, user_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_review_check(self) -> list[Order]:
        """Orders whose event_date passed 1+ day ago and no review sent yet."""
        cutoff = datetime.utcnow() - timedelta(days=1)
        result = await self.session.execute(
            select(Order)
            .where(Order.event_date <= cutoff, Order.status == OrderStatus.DONE)
            .options(selectinload(Order.review))
        )
        orders = list(result.scalars().all())
        return [o for o in orders if o.review is None or not o.review.review_sent]

    async def get_recent_for_report(self, days: int = 30) -> list[Order]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Order)
            .where(Order.created_at >= cutoff)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())


class ReviewRepository(BaseRepository[Review]):
    model = Review

    async def create_for_order(self, order_id: int, user_id: int) -> Review:
        review = Review(order_id=order_id, user_id=user_id, review_sent=True)
        self.session.add(review)
        await self.session.flush()
        return review

    async def get_by_order(self, order_id: int) -> Review | None:
        result = await self.session.execute(
            select(Review).where(Review.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def submit(self, review_id: int, rating: int, text: str | None) -> None:
        review = await self.get_by_id(review_id)
        if review:
            review.rating = rating
            review.text = text
            review.review_created_at = datetime.utcnow()
            await self.session.flush()
