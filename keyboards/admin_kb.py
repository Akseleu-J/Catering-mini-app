"""keyboards/admin_kb.py — Admin panel inline keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Категории", callback_data="admin_cats"),
         InlineKeyboardButton(text="🍽 Продукты", callback_data="admin_products")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders"),
         InlineKeyboardButton(text="📊 Отчёт Excel", callback_data="admin_report")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔚 Выйти", callback_data="main")],
    ])


def admin_categories_kb(categories: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{c.emoji} {c.name}", callback_data=f"admin_cat_{c.id}")]
        for c in categories
    ]
    buttons += [
        [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_add_cat")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_cat_actions_kb(cat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Название", callback_data=f"admin_cat_edit_name_{cat_id}"),
         InlineKeyboardButton(text="😀 Эмодзи", callback_data=f"admin_cat_edit_emoji_{cat_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_cat_del_{cat_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_cats")],
    ])


def admin_products_select_cat_kb(categories: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{c.emoji} {c.name}", callback_data=f"admin_prod_cat_{c.id}")]
        for c in categories
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_products_kb(products: list, cat_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        status = "✅" if p.is_available else "🚫"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {p.name} — {int(p.price):,} ₸",
            callback_data=f"admin_prod_{p.id}",
        )])
    buttons += [
        [InlineKeyboardButton(text="➕ Добавить продукт", callback_data=f"admin_add_prod_{cat_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_products")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_product_actions_kb(product_id: int, cat_id: int, is_available: bool) -> InlineKeyboardMarkup:
    toggle_text = "🚫 В стоп-лист" if is_available else "✅ Активировать"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Цена", callback_data=f"admin_prod_price_{product_id}"),
         InlineKeyboardButton(text="🖼 Фото", callback_data=f"admin_prod_photo_{product_id}")],
        [InlineKeyboardButton(text="📝 Название", callback_data=f"admin_prod_name_{product_id}"),
         InlineKeyboardButton(text="📄 Описание", callback_data=f"admin_prod_desc_{product_id}")],
        [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_prod_toggle_{product_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_prod_del_{product_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_prod_cat_{cat_id}")],
    ])


def admin_confirm_kb(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=yes_cb),
         InlineKeyboardButton(text="❌ Нет", callback_data=no_cb)],
    ])


def admin_orders_kb(orders: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"#{o.order_uid} {o.event_date.strftime('%d.%m')} — {int(o.total_price):,} ₸ [{o.status}]",
            callback_data=f"admin_order_{o.id}",
        )]
        for o in orders
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_order_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_ord_confirm_{order_id}"),
         InlineKeyboardButton(text="✔️ Выполнен", callback_data=f"admin_ord_done_{order_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_orders")],
    ])


def admin_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Отправить всем", callback_data="admin_broadcast_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_main")],
    ])


def admin_cancel_kb(back: str = "admin_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=back)],
    ])
