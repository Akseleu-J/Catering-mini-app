"""handlers/checkout.py — Full FSM checkout: name → date → time → location → confirm."""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.order_service import OrderService, OrderValidationError
from services.cart_service import CartService
from keyboards.user_kb import checkout_confirm_kb, order_done_kb, cancel_kb
from utils.formatters import fmt_cart_summary, fmt_order_summary
from utils.date_parser import parse_date, parse_time, combine_datetime
from states import CheckoutFSM
from config import settings, get_logger

logger = get_logger(__name__)
router = Router()


@router.callback_query(F.data == "checkout")
async def cb_checkout_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    service = CartService(session)
    cart = await service.get_cart_summary(callback.from_user.id)
    if not cart["items"]:
        await callback.answer("🛒 Корзина пуста!", show_alert=True)
        return
    await state.set_state(CheckoutFSM.waiting_name)
    await callback.message.edit_text(
        f"{fmt_cart_summary(cart)}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📝 *Шаг 1/4 — Ваше имя:*\nКак к вам обращаться?",
        parse_mode="Markdown",
        reply_markup=cancel_kb("cart"),
    )
    await callback.answer()


@router.callback_query(F.data == "checkout_restart")
async def cb_checkout_restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Оформление отменено. Корзина сохранена.",
        reply_markup=cancel_kb("cart"),
    )
    await callback.answer()


@router.message(CheckoutFSM.waiting_name)
async def msg_checkout_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Введите имя (минимум 2 символа).", reply_markup=cancel_kb("cart"))
        return
    await state.update_data(client_name=name)
    await state.set_state(CheckoutFSM.waiting_date)
    await message.answer(
        f"✅ Имя: *{name}*\n\n"
        "📅 *Шаг 2/4 — Дата мероприятия:*\nФормат: `ДД.ММ.ГГГГ` (например: `25.06.2025`)",
        parse_mode="Markdown",
        reply_markup=cancel_kb("cart"),
    )


@router.message(CheckoutFSM.waiting_date)
async def msg_checkout_date(message: Message, state: FSMContext):
    dt = parse_date(message.text or "")
    if not dt:
        await message.answer(
            "❌ Неверный формат. Введите дату в формате `ДД.ММ.ГГГГ`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
        return
    await state.update_data(event_date=dt)
    await state.set_state(CheckoutFSM.waiting_time)
    await message.answer(
        f"✅ Дата: *{dt.strftime('%d.%m.%Y')}*\n\n"
        "⏰ *Шаг 3/4 — Время начала:*\nФормат: `ЧЧ:ММ` (например: `14:00`)",
        parse_mode="Markdown",
        reply_markup=cancel_kb("cart"),
    )


@router.message(CheckoutFSM.waiting_time)
async def msg_checkout_time(message: Message, state: FSMContext):
    parsed = parse_time(message.text or "")
    if not parsed:
        await message.answer(
            "❌ Неверный формат. Введите время в формате `ЧЧ:ММ`",
            parse_mode="Markdown",
            reply_markup=cancel_kb("cart"),
        )
        return
    hour, minute = parsed
    data = await state.get_data()
    event_dt = combine_datetime(data["event_date"], hour, minute)

    # Validate lead time
    try:
        from services.order_service import OrderService
        OrderService(None).validate_event_datetime(event_dt)
    except OrderValidationError as e:
        await message.answer(str(e), reply_markup=cancel_kb("cart"))
        return

    await state.update_data(event_datetime=event_dt)
    await state.set_state(CheckoutFSM.waiting_location)
    await message.answer(
        f"✅ Время: *{hour:02d}:{minute:02d}*\n\n"
        "📍 *Шаг 4/4 — Адрес / локация:*\nНапример: `ул. Байтурсынова 5, зал «Алтын»`",
        parse_mode="Markdown",
        reply_markup=cancel_kb("cart"),
    )


@router.message(CheckoutFSM.waiting_location)
async def msg_checkout_location(message: Message, state: FSMContext, session: AsyncSession):
    location = (message.text or "").strip()
    if len(location) < 3:
        await message.answer("❌ Введите адрес (минимум 3 символа).", reply_markup=cancel_kb("cart"))
        return
    await state.update_data(location=location)
    await state.set_state(CheckoutFSM.confirming)

    data = await state.get_data()
    cart_service = CartService(session)
    cart = await cart_service.get_cart_summary(message.from_user.id)

    summary = fmt_cart_summary(cart)
    confirm_text = (
        f"📋 *Проверьте заказ:*\n\n"
        f"👤 Имя: *{data['client_name']}*\n"
        f"📅 Дата: *{data['event_datetime'].strftime('%d.%m.%Y')}*\n"
        f"⏰ Время: *{data['event_datetime'].strftime('%H:%M')}*\n"
        f"📍 Адрес: *{location}*\n\n"
        f"{summary}"
    )
    await message.answer(
        confirm_text,
        parse_mode="Markdown",
        reply_markup=checkout_confirm_kb(),
    )


@router.callback_query(F.data == "checkout_confirm", CheckoutFSM.confirming)
async def cb_checkout_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    service = OrderService(session)
    try:
        order = await service.checkout(
            user_id=callback.from_user.id,
            client_name=data["client_name"],
            event_date=data["event_datetime"],
            location=data["location"],
        )
    except OrderValidationError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await state.clear()
    whatsapp_link = await service.get_whatsapp_link(order)

    # Notify admin
    try:
        from models.base import AsyncSessionLocal
        async with AsyncSessionLocal() as admin_session:
            from repositories import OrderRepository
            full_order = await OrderRepository(admin_session).get_with_items(order.id)
            admin_text = (
                f"🔔 *НОВЫЙ ЗАКАЗ #{order.order_uid}*\n\n"
                f"{fmt_order_summary(full_order)}\n\n"
                f"👤 TG: @{callback.from_user.username or callback.from_user.id}"
            )
            await callback.bot.send_message(settings.admin_id, admin_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

    await callback.message.edit_text(
        f"✅ *Заказ #{order.order_uid} оформлен!*\n\n"
        f"Наш менеджер свяжется с вами для подтверждения.\n"
        f"Или нажмите кнопку ниже, чтобы написать в WhatsApp прямо сейчас 👇",
        parse_mode="Markdown",
        reply_markup=order_done_kb(whatsapp_link),
    )
    await callback.answer("✅ Заказ оформлен!")
    logger.info(f"Order #{order.order_uid} confirmed by user {callback.from_user.id}")
