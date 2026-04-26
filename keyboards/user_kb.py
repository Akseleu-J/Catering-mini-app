"""keyboards/user_kb.py — User-facing inline keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Меню",        callback_data="menu"),
         InlineKeyboardButton(text="🛒 Корзина",     callback_data="cart")],
        [InlineKeyboardButton(text="📋 Мои заказы",  callback_data="my_orders"),
         InlineKeyboardButton(text="🤖 AI Помощник", callback_data="ai_chat")],
        [InlineKeyboardButton(text="📞 Связаться",   callback_data="contact")],
    ])


def categories_kb(categories: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{c.emoji} {c.name}",
            callback_data=f"cat_{c.id}",
        )]
        for c in categories
    ]
    buttons.append([InlineKeyboardButton(text="🏠 Главная", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_kb(products: list, cat_id: int, page: int, total: int, per_page: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"🍽 {p.name}  —  {int(p.price):,} ₸",
            callback_data=f"product_{p.id}",
        )]
        for p in products
    ]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"cat_{cat_id}_page_{page - 1}"))
    if (page + 1) * per_page < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"cat_{cat_id}_page_{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="⬅️ Категории", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_kb(product_id: int, cat_id: int) -> InlineKeyboardMarkup:
    """
    Карточка товара — сразу показываем два способа добавления:
    🧮 За штуки  |  👥 За человека
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧮 Добавить (штуки)",
                callback_data=f"add_manual_{product_id}",
            ),
            InlineKeyboardButton(
                text="👥 Добавить (по гостям)",
                callback_data=f"add_guests_{product_id}",
            ),
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{cat_id}")],
    ])


def add_to_cart_mode_kb(product_id: int) -> InlineKeyboardMarkup:
    """Fallback — отдельный экран выбора режима (если нужен)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🧮 Вручную (штуки)",
            callback_data=f"add_manual_{product_id}",
        )],
        [InlineKeyboardButton(
            text="👥 По количеству гостей",
            callback_data=f"add_guests_{product_id}",
        )],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"product_{product_id}")],
    ])


def cart_kb(cart_items: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"❌ {row['product'].name}",
            callback_data=f"remove_{row['product'].id}",
        )]
        for row in cart_items
    ]
    if cart_items:
        buttons.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")])
        buttons.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")])
    buttons.append([InlineKeyboardButton(text="🍽 В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def checkout_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="checkout_confirm")],
        [InlineKeyboardButton(text="✏️ Изменить",          callback_data="checkout_restart")],
        [InlineKeyboardButton(text="❌ Отмена",             callback_data="cart")],
    ])


def order_done_kb(whatsapp_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в WhatsApp", url=whatsapp_link)],
        [InlineKeyboardButton(text="📋 Мои заказы",          callback_data="my_orders")],
        [InlineKeyboardButton(text="🏠 Главная",             callback_data="main")],
    ])


def my_orders_kb(orders: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"#{o.order_uid} — {o.event_date.strftime('%d.%m')} — {int(o.total_price):,} ₸",
            callback_data=f"order_{o.id}",
        )]
        for o in orders
    ]
    buttons.append([InlineKeyboardButton(text="🏠 Главная", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_detail_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить заказ", callback_data=f"repeat_{order_id}")],
        [InlineKeyboardButton(text="⬅️ Мои заказы",      callback_data="my_orders")],
    ])


def review_rating_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐",     callback_data=f"review_{order_id}_1"),
         InlineKeyboardButton(text="⭐⭐",   callback_data=f"review_{order_id}_2"),
         InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"review_{order_id}_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐",   callback_data=f"review_{order_id}_4"),
         InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"review_{order_id}_5")],
        [InlineKeyboardButton(text="Пропустить", callback_data=f"review_skip_{order_id}")],
    ])


def review_text_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data=f"review_done_{order_id}")],
    ])


def cancel_kb(back_cb: str = "main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=back_cb)],
    ])
