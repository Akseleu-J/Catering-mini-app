"""utils/formatters.py — Text formatting helpers."""

from datetime import datetime
from models.models import Order


def fmt_order_summary(order: Order) -> str:
    lines = [
        f"📋 *Заказ #{order.order_uid}*",
        f"👤 {order.client_name}",
        f"📅 {order.event_date.strftime('%d.%m.%Y %H:%M')}",
        f"📍 {order.location}",
        "",
        "🍽 *Состав:*",
    ]
    for item in order.items:
        subtotal = int(item.quantity * item.unit_price)
        lines.append(f"  • {item.product_name} × {item.quantity} — {subtotal:,} ₸")
    lines += ["", f"💰 *Итого: {int(order.total_price):,} ₸*"]
    return "\n".join(lines)


def fmt_cart_summary(cart: dict) -> str:
    if not cart["items"]:
        return "🛒 Корзина пуста"
    lines = ["🛒 *Ваша корзина:*", ""]
    for row in cart["items"]:
        p = row["product"]
        subtotal = int(row["subtotal"])
        mode_tag = f" (👥 {row['guests_count']} гост.)" if row["calc_mode"] == "per_person" else ""
        lines.append(f"• *{p.name}* × {row['quantity']}{mode_tag} — {subtotal:,} ₸")
    lines += ["", f"💰 *Итого: {int(cart['total']):,} ₸*"]
    return "\n".join(lines)


def fmt_product_card(product) -> str:
    status = "✅ Доступно" if product.is_available else "🚫 Стоп-лист"
    return (
        f"🍽 *{product.name}*\n\n"
        f"📝 {product.description or 'Описание отсутствует'}\n\n"
        f"💰 Цена: *{int(product.price):,} ₸*\n"
        f"👥 1 порция на: *{product.serving_factor} чел.*\n"
        f"📊 Статус: {status}"
    )
