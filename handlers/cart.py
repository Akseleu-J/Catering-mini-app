"""handlers/cart.py — Cart management + dual calculation engine. Fixed filters."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.cart_service import CartService
from keyboards.user_kb import cart_kb, cancel_kb
from utils.formatters import fmt_cart_summary
from states import CartAddFSM

router = Router()


# ── View Cart ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cart")
async def cb_cart(callback: CallbackQuery, session: AsyncSession):
    service = CartService(session)
    cart    = await service.get_cart_summary(callback.from_user.id)
    text    = fmt_cart_summary(cart)
    try:
        await callback.message.edit_text(
            text, parse_mode="Markdown",
            reply_markup=cart_kb(cart["items"]),
        )
    except Exception:
        await callback.message.answer(
            text, parse_mode="Markdown",
            reply_markup=cart_kb(cart["items"]),
        )
    await callback.answer()


# ── Add: Manual quantity ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("add_manual_"))
async def cb_add_manual_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.set_state(CartAddFSM.waiting_quantity)
    await state.update_data(product_id=product_id)
    try:
        await callback.message.edit_text(
            "✏️ *Введите количество порций:*\nНапример: `3`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
    except Exception:
        await callback.message.answer(
            "✏️ *Введите количество порций:*\nНапример: `3`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
    await callback.answer()


@router.message(CartAddFSM.waiting_quantity)
async def msg_add_manual_quantity(message: Message, state: FSMContext, session: AsyncSession):
    raw = (message.text or "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer(
            "❌ Введите целое число больше 0.\nНапример: `5`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
        return
    data    = await state.get_data()
    service = CartService(session)
    result  = await service.add_manual(message.from_user.id, data["product_id"], int(raw))
    await state.clear()
    await message.answer(result, parse_mode="Markdown", reply_markup=cancel_kb("cart"))


# ── Add: Per-person calculation ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("add_guests_"))
async def cb_add_guests_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.set_state(CartAddFSM.waiting_guests)
    await state.update_data(product_id=product_id)
    try:
        await callback.message.edit_text(
            "👥 *Сколько гостей будет на мероприятии?*\n\n"
            "Бот автоматически рассчитает нужное количество порций.\n"
            "Например: `50`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
    except Exception:
        await callback.message.answer(
            "👥 *Сколько гостей будет на мероприятии?*\nНапример: `50`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
    await callback.answer()


@router.message(CartAddFSM.waiting_guests)
async def msg_add_guests(message: Message, state: FSMContext, session: AsyncSession):
    raw = (message.text or "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        await message.answer(
            "❌ Введите целое число больше 0.\nНапример: `50`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
        return
    data    = await state.get_data()
    service = CartService(session)
    result  = await service.add_per_person(message.from_user.id, data["product_id"], int(raw))
    await state.clear()
    await message.answer(result, parse_mode="Markdown", reply_markup=cancel_kb("cart"))


# ── Remove item ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("remove_"))
async def cb_remove_item(callback: CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split("_")[1])
    service    = CartService(session)
    await service.remove_item(callback.from_user.id, product_id)
    cart = await service.get_cart_summary(callback.from_user.id)
    text = fmt_cart_summary(cart)
    try:
        await callback.message.edit_text(
            text, parse_mode="Markdown",
            reply_markup=cart_kb(cart["items"]),
        )
    except Exception:
        await callback.message.answer(
            text, parse_mode="Markdown",
            reply_markup=cart_kb(cart["items"]),
        )
    await callback.answer("✅ Удалено")


# ── Clear cart ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "clear_cart")
async def cb_clear_cart(callback: CallbackQuery, session: AsyncSession):
    service = CartService(session)
    await service.clear(callback.from_user.id)
    try:
        await callback.message.edit_text(
            "🗑 *Корзина очищена.*",
            parse_mode="Markdown",
            reply_markup=cancel_kb("menu"),
        )
    except Exception:
        await callback.message.answer(
            "🗑 *Корзина очищена.*",
            parse_mode="Markdown",
            reply_markup=cancel_kb("menu"),
        )
    await callback.answer("Корзина очищена")
