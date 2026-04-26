"""handlers/admin.py — Full admin panel: categories, products, orders, reports."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import CategoryRepository, ProductRepository, OrderRepository
from services.report_service import generate_excel_report
from keyboards.admin_kb import (
    admin_main_kb, admin_categories_kb, admin_cat_actions_kb,
    admin_products_select_cat_kb, admin_products_kb, admin_product_actions_kb,
    admin_confirm_kb, admin_orders_kb, admin_order_actions_kb, admin_cancel_kb,
)
from states import AdminCategoryFSM, AdminProductFSM
from config import settings, get_logger

logger = get_logger(__name__)
router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


# ══════════════════════════════════════════════════════════════
#  ENTRY
# ══════════════════════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return
    await state.clear()
    await message.answer(
        "👨‍💼 *Панель администратора*\n\nВыберите раздел:",
        parse_mode="Markdown",
        reply_markup=admin_main_kb(),
    )


@router.callback_query(F.data == "admin_main")
async def cb_admin_main(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    await state.clear()
    await callback.message.edit_text(
        "👨‍💼 *Панель администратора*",
        parse_mode="Markdown",
        reply_markup=admin_main_kb(),
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════════
#  CATEGORIES
# ══════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_cats")
async def cb_admin_cats(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    await state.clear()
    cats = await CategoryRepository(session).get_all_with_counts()
    await callback.message.edit_text(
        "📂 *Категории*", parse_mode="Markdown",
        reply_markup=admin_categories_kb(cats),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_cat_(\d+)$"))
async def cb_admin_cat_view(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    cat_id = int(callback.data.split("_")[2])
    cat = await CategoryRepository(session).get_by_id(cat_id)
    await callback.message.edit_text(
        f"{cat.emoji} *{cat.name}*\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_cat_actions_kb(cat_id),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_cat")
async def cb_admin_add_cat(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    await state.set_state(AdminCategoryFSM.waiting_name)
    await callback.message.edit_text(
        "📂 *Новая категория*\n\nВведите название:",
        parse_mode="Markdown", reply_markup=admin_cancel_kb(),
    )
    await callback.answer()


@router.message(AdminCategoryFSM.waiting_name)
async def msg_admin_cat_name(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id): return
    await state.update_data(cat_name=message.text.strip())
    await state.set_state(AdminCategoryFSM.waiting_emoji)
    await message.answer("😀 Введите эмодзи (например: 🍽):", reply_markup=admin_cancel_kb())


@router.message(AdminCategoryFSM.waiting_emoji)
async def msg_admin_cat_emoji(message: Message, state: FSMContext, session: AsyncSession):
    if not _is_admin(message.from_user.id): return
    data = await state.get_data()
    repo = CategoryRepository(session)
    cat = await repo.create(name=data["cat_name"], emoji=message.text.strip() or "🍽")
    await state.clear()
    await message.answer(
        f"✅ Категория *{cat.emoji} {cat.name}* добавлена!",
        parse_mode="Markdown", reply_markup=admin_main_kb(),
    )


@router.callback_query(F.data.regexp(r"^admin_cat_del_(\d+)$"))
async def cb_admin_cat_del(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    cat_id = int(callback.data.rsplit("_", 1)[1])
    await CategoryRepository(session).delete_by_id(cat_id)
    await callback.message.edit_text("✅ Категория удалена.", reply_markup=admin_main_kb())
    await callback.answer("✅ Удалено")


# ══════════════════════════════════════════════════════════════
#  PRODUCTS
# ══════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_products")
async def cb_admin_products(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    await state.clear()
    cats = await CategoryRepository(session).get_active()
    await callback.message.edit_text(
        "🍽 *Продукты — выберите категорию:*",
        parse_mode="Markdown",
        reply_markup=admin_products_select_cat_kb(cats),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_prod_cat_(\d+)$"))
async def cb_admin_prod_cat(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    cat_id = int(callback.data.rsplit("_", 1)[1])
    products = await ProductRepository(session).get_by_category(cat_id, available_only=False)
    await callback.message.edit_text(
        "🍽 *Продукты:*", parse_mode="Markdown",
        reply_markup=admin_products_kb(products, cat_id),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_prod_(\d+)$"))
async def cb_admin_prod_view(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    prod_id = int(callback.data.rsplit("_", 1)[1])
    p = await ProductRepository(session).get_by_id(prod_id)
    status = "✅ Активен" if p.is_available else "🚫 Стоп-лист"
    text = (
        f"*{p.name}*\n"
        f"💰 {int(p.price):,} ₸ | 👥 {p.serving_factor} чел/порция\n"
        f"📊 {status}\n"
        f"📝 {p.description or '—'}"
    )
    await callback.message.edit_text(
        text, parse_mode="Markdown",
        reply_markup=admin_product_actions_kb(prod_id, p.category_id, p.is_available),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_prod")
@router.callback_query(F.data.regexp(r"^admin_add_prod_(\d+)$"))
async def cb_admin_add_prod(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    parts = callback.data.split("_")
    cat_id = int(parts[-1]) if len(parts) > 3 else None
    if not cat_id:
        cats = await CategoryRepository(session).get_active()
        await callback.message.edit_text(
            "Выберите категорию:", reply_markup=admin_products_select_cat_kb(cats)
        )
        await callback.answer(); return
    await state.set_state(AdminProductFSM.waiting_name)
    await state.update_data(category_id=cat_id)
    await callback.message.edit_text(
        "➕ *Новый продукт*\n\n📝 *Шаг 1/5* — Введите название:",
        parse_mode="Markdown", reply_markup=admin_cancel_kb(f"admin_prod_cat_{cat_id}"),
    )
    await callback.answer()


@router.message(AdminProductFSM.waiting_name)
async def msg_admin_prod_name(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id): return
    await state.update_data(prod_name=message.text.strip())
    await state.set_state(AdminProductFSM.waiting_description)
    await message.answer("📄 *Шаг 2/5* — Описание продукта:", parse_mode="Markdown", reply_markup=admin_cancel_kb())


@router.message(AdminProductFSM.waiting_description)
async def msg_admin_prod_desc(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id): return
    await state.update_data(prod_desc=message.text.strip())
    await state.set_state(AdminProductFSM.waiting_price)
    await message.answer("💰 *Шаг 3/5* — Цена (тенге, только число):", parse_mode="Markdown", reply_markup=admin_cancel_kb())


@router.message(AdminProductFSM.waiting_price)
async def msg_admin_prod_price(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id): return
    try:
        price = float(message.text.strip().replace(" ", ""))
        if price <= 0: raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену."); return
    await state.update_data(prod_price=price)
    await state.set_state(AdminProductFSM.waiting_serving)
    await message.answer(
        "👥 *Шаг 4/5* — Сколько человек обслуживает 1 порция?\n(например: `10`)",
        parse_mode="Markdown", reply_markup=admin_cancel_kb(),
    )


@router.message(AdminProductFSM.waiting_serving)
async def msg_admin_prod_serving(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id): return
    raw = message.text.strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer("❌ Введите целое число > 0."); return
    await state.update_data(serving_factor=int(raw))
    await state.set_state(AdminProductFSM.waiting_photo)
    await message.answer("🖼 *Шаг 5/5* — Отправьте фото продукта:", parse_mode="Markdown", reply_markup=admin_cancel_kb())


@router.message(AdminProductFSM.waiting_photo, F.photo)
async def msg_admin_prod_photo(message: Message, state: FSMContext, session: AsyncSession):
    if not _is_admin(message.from_user.id): return
    data = await state.get_data()
    repo = ProductRepository(session)
    product = await repo.create(
        category_id=data["category_id"],
        name=data["prod_name"],
        description=data["prod_desc"],
        price=data["prod_price"],
        serving_factor=data["serving_factor"],
        photo_file_id=message.photo[-1].file_id,
    )
    await state.clear()
    await message.answer_photo(
        photo=message.photo[-1].file_id,
        caption=f"✅ *{product.name}* добавлен!\n💰 {int(product.price):,} ₸",
        parse_mode="Markdown", reply_markup=admin_main_kb(),
    )


@router.message(AdminProductFSM.waiting_photo)
async def msg_admin_prod_photo_bad(message: Message):
    if not _is_admin(message.from_user.id): return
    await message.answer("❌ Отправьте именно фото.")


# ── Toggle availability ───────────────────────────────────────

@router.callback_query(F.data.regexp(r"^admin_prod_toggle_(\d+)$"))
async def cb_admin_prod_toggle(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    prod_id = int(callback.data.rsplit("_", 1)[1])
    new_state = await ProductRepository(session).toggle_availability(prod_id)
    status = "✅ Активен" if new_state else "🚫 В стоп-листе"
    await callback.answer(f"Статус изменён: {status}", show_alert=True)
    p = await ProductRepository(session).get_by_id(prod_id)
    await callback.message.edit_reply_markup(
        reply_markup=admin_product_actions_kb(prod_id, p.category_id, p.is_available)
    )


# ── Edit price ───────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^admin_prod_price_(\d+)$"))
async def cb_admin_edit_price(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    prod_id = int(callback.data.rsplit("_", 1)[1])
    await state.set_state(AdminProductFSM.editing_price)
    await state.update_data(prod_id=prod_id)
    await callback.message.edit_text(
        "💰 *Новая цена (тенге):*", parse_mode="Markdown",
        reply_markup=admin_cancel_kb(f"admin_prod_{prod_id}"),
    )
    await callback.answer()


@router.message(AdminProductFSM.editing_price)
async def msg_admin_edit_price(message: Message, state: FSMContext, session: AsyncSession):
    if not _is_admin(message.from_user.id): return
    try:
        price = float(message.text.strip().replace(" ", ""))
        if price <= 0: raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную цену."); return
    data = await state.get_data()
    await ProductRepository(session).update_by_id(data["prod_id"], price=price)
    await state.clear()
    await message.answer(f"✅ Цена обновлена: *{int(price):,} ₸*", parse_mode="Markdown", reply_markup=admin_main_kb())


# ── Edit photo ────────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^admin_prod_photo_(\d+)$"))
async def cb_admin_edit_photo(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    prod_id = int(callback.data.rsplit("_", 1)[1])
    await state.set_state(AdminProductFSM.editing_photo)
    await state.update_data(prod_id=prod_id)
    await callback.message.edit_text(
        "🖼 *Отправьте новое фото:*", parse_mode="Markdown",
        reply_markup=admin_cancel_kb(f"admin_prod_{prod_id}"),
    )
    await callback.answer()


@router.message(AdminProductFSM.editing_photo, F.photo)
async def msg_admin_edit_photo(message: Message, state: FSMContext, session: AsyncSession):
    if not _is_admin(message.from_user.id): return
    data = await state.get_data()
    await ProductRepository(session).update_by_id(data["prod_id"], photo_file_id=message.photo[-1].file_id)
    await state.clear()
    await message.answer("✅ Фото обновлено!", reply_markup=admin_main_kb())


# ── Delete product ────────────────────────────────────────────

@router.callback_query(F.data.regexp(r"^admin_prod_del_(\d+)$"))
async def cb_admin_prod_del(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    prod_id = int(callback.data.rsplit("_", 1)[1])
    await ProductRepository(session).delete_by_id(prod_id)
    await callback.message.edit_text("✅ Продукт удалён.", reply_markup=admin_main_kb())
    await callback.answer("✅ Удалено")


# ══════════════════════════════════════════════════════════════
#  ORDERS
# ══════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_orders")
async def cb_admin_orders(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    orders = await OrderRepository(session).get_recent_for_report(days=30)
    if not orders:
        await callback.answer("Заказов нет.", show_alert=True); return
    await callback.message.edit_text(
        "📋 *Последние заказы:*", parse_mode="Markdown",
        reply_markup=admin_orders_kb(orders),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_order_(\d+)$"))
async def cb_admin_order_view(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    order_id = int(callback.data.rsplit("_", 1)[1])
    order = await OrderRepository(session).get_with_items(order_id)
    from utils.formatters import fmt_order_summary
    await callback.message.edit_text(
        fmt_order_summary(order), parse_mode="Markdown",
        reply_markup=admin_order_actions_kb(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_ord_confirm_(\d+)$"))
async def cb_admin_ord_confirm(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    order_id = int(callback.data.rsplit("_", 1)[1])
    from services.order_service import OrderService
    await OrderService(session).mark_confirmed(order_id)
    await callback.answer("✅ Заказ подтверждён", show_alert=True)


@router.callback_query(F.data.regexp(r"^admin_ord_done_(\d+)$"))
async def cb_admin_ord_done(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    order_id = int(callback.data.rsplit("_", 1)[1])
    from services.order_service import OrderService
    await OrderService(session).mark_done(order_id)
    await callback.answer("✅ Статус: Выполнен", show_alert=True)


# ══════════════════════════════════════════════════════════════
#  EXCEL REPORT
# ══════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_report")
async def cb_admin_report(callback: CallbackQuery, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    await callback.answer("⏳ Генерирую отчёт...")
    orders = await OrderRepository(session).get_recent_for_report(days=30)
    excel_bytes = generate_excel_report(orders)
    from datetime import datetime
    filename = f"report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    await callback.message.answer_document(
        BufferedInputFile(excel_bytes, filename=filename),
        caption=f"📊 Отчёт за последние 30 дней\n📦 Заказов: {len(orders)}",
    )
    logger.info(f"Admin {callback.from_user.id} generated Excel report")
