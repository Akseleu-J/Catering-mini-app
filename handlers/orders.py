"""handlers/orders.py — My orders view + repeat order. Fixed filters."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.order_service import OrderService
from repositories import OrderRepository
from keyboards.user_kb import my_orders_kb, order_detail_kb, cancel_kb
from utils.formatters import fmt_order_summary

router = Router()


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(callback: CallbackQuery, session: AsyncSession):
    repo   = OrderRepository(session)
    orders = await repo.get_user_orders(callback.from_user.id)
    if not orders:
        try:
            await callback.message.edit_text(
                "📋 *У вас пока нет заказов.*\n\nОформите первый через меню!",
                parse_mode="Markdown",
                reply_markup=cancel_kb("main"),
            )
        except Exception:
            await callback.message.answer(
                "📋 *У вас пока нет заказов.*",
                parse_mode="Markdown",
                reply_markup=cancel_kb("main"),
            )
        await callback.answer()
        return
    try:
        await callback.message.edit_text(
            "📋 *Ваши заказы:*\n\nВыберите заказ для подробностей:",
            parse_mode="Markdown",
            reply_markup=my_orders_kb(orders),
        )
    except Exception:
        await callback.message.answer(
            "📋 *Ваши заказы:*",
            parse_mode="Markdown",
            reply_markup=my_orders_kb(orders),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("order_"))
async def cb_order_detail(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[1])
    repo     = OrderRepository(session)
    order    = await repo.get_with_items(order_id)
    if not order or order.user_id != callback.from_user.id:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    try:
        await callback.message.edit_text(
            fmt_order_summary(order),
            parse_mode="Markdown",
            reply_markup=order_detail_kb(order_id),
        )
    except Exception:
        await callback.message.answer(
            fmt_order_summary(order),
            parse_mode="Markdown",
            reply_markup=order_detail_kb(order_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("repeat_"))
async def cb_repeat_order(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[1])
    service  = OrderService(session)
    result   = await service.repeat_order(callback.from_user.id, order_id)
    await callback.answer(result, show_alert=True)
