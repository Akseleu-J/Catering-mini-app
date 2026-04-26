"""handlers/ai_handler.py — Gemini AI assistant integration."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.ai_service import ai_service
from keyboards.user_kb import cancel_kb

router = Router()
AI_STATE_KEY = "in_ai_chat"


@router.callback_query(F.data == "ai_chat")
async def cb_ai_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(**{AI_STATE_KEY: True})
    await callback.message.edit_text(
        "🤖 *AI-Ассистент активирован*\n\n"
        "Задайте вопрос о нашем меню, ценах или услугах.\n"
        "Для выхода — нажмите «Выйти».",
        parse_mode="Markdown",
        reply_markup=cancel_kb("main"),
    )
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def msg_ai_fallback(message: Message, state: FSMContext):
    """Catch all non-command text messages as AI questions."""
    data = await state.get_data()
    if not data.get(AI_STATE_KEY):
        return  # Not in AI mode, ignore

    await message.chat.do("typing")
    response = await ai_service.ask(message.from_user.id, message.text)
    await message.answer(
        response,
        reply_markup=cancel_kb("main"),
    )
