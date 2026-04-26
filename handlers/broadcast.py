"""handlers/broadcast.py — Broadcast messages to all active users."""

import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import UserRepository
from keyboards.admin_kb import admin_broadcast_confirm_kb, admin_cancel_kb, admin_main_kb
from states import AdminBroadcastFSM
from config import settings, get_logger

logger = get_logger(__name__)
router = Router()


def _is_admin(uid: int) -> bool:
    return uid == settings.admin_id


@router.callback_query(F.data == "admin_broadcast")
async def cb_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return
    await state.set_state(AdminBroadcastFSM.waiting_message)
    await callback.message.edit_text(
        "📢 *Рассылка*\n\nОтправьте сообщение (текст, фото, видео) — оно уйдёт всем активным пользователям.",
        parse_mode="Markdown",
        reply_markup=admin_cancel_kb(),
    )
    await callback.answer()


@router.message(AdminBroadcastFSM.waiting_message)
async def msg_broadcast_preview(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id): return
    # Store message_id for forwarding
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await state.set_state(AdminBroadcastFSM.confirming)
    await message.answer(
        "👆 *Предпросмотр выше.*\n\nОтправить это сообщение всем пользователям?",
        parse_mode="Markdown",
        reply_markup=admin_broadcast_confirm_kb(),
    )


@router.callback_query(F.data == "admin_broadcast_send", AdminBroadcastFSM.confirming)
async def cb_broadcast_send(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True); return

    data = await state.get_data()
    await state.clear()

    users = await UserRepository(session).get_all_active()
    total = len(users)

    await callback.message.edit_text(f"📤 Начинаю рассылку {total} пользователям...")
    await callback.answer()

    sent = 0
    blocked = 0

    for user in users:
        try:
            await callback.bot.forward_message(
                chat_id=user.id,
                from_chat_id=data["from_chat_id"],
                message_id=data["message_id"],
            )
            sent += 1
            await asyncio.sleep(0.05)  # Respect Telegram rate limits (~20 msg/sec)
        except Exception as e:
            err = str(e).lower()
            if "forbidden" in err or "blocked" in err or "deactivated" in err:
                await UserRepository(session).mark_blocked(user.id)
                blocked += 1
            else:
                logger.error(f"Broadcast error for user {user.id}: {e}")

    await session.commit()

    result_text = (
        f"✅ *Рассылка завершена!*\n\n"
        f"📤 Отправлено: *{sent}*\n"
        f"🚫 Заблокировали бот: *{blocked}*\n"
        f"👥 Всего адресатов: *{total}*"
    )
    await callback.message.edit_text(result_text, parse_mode="Markdown", reply_markup=admin_main_kb())
    logger.info(f"Broadcast done: sent={sent}, blocked={blocked}, total={total}")
