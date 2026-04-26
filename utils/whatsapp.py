"""utils/whatsapp.py — WhatsApp link generator."""

from urllib.parse import quote
from models.models import Order


def build_whatsapp_link(order: Order, phone: str) -> str:
    lines = [
        f"🎉 *Новый заказ #{order.order_uid}*",
        f"👤 Клиент: {order.client_name}",
        f"📅 Дата мероприятия: {order.event_date.strftime('%d.%m.%Y %H:%M')}",
        f"📍 Локация: {order.location}",
        "",
        "🍽 *Состав заказа:*",
    ]
    for item in order.items:
        lines.append(f"  • {item.product_name} × {item.quantity} = {int(item.quantity * item.unit_price):,} ₸")
    lines += ["", f"💰 *Итого: {int(order.total_price):,} ₸*"]
    text = "\n".join(lines)
    return f"https://wa.me/{phone}?text={quote(text)}"
