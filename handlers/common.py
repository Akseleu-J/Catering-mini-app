"""handlers/common.py — /start and main navigation."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.user_kb import main_menu_kb
from config import settings

router = Router()

WELCOME = (
    "🌟 *Добро пожаловать в Qazaq Catering!*\n\n"
    "Мы создаём незабываемые праздники в Шымкенте.\n\n"
    "🍽 Казахская и европейская кухня\n"
    "🎉 Тои, свадьбы, корпоративы\n"
    "🚚 Выездной сервис по городу\n\n"
    "Выберите действие 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME, parse_mode="Markdown", reply_markup=main_menu_kb())


@router.callback_query(F.data == "main")
async def cb_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "contact")
async def cb_contact(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📞 *Свяжитесь с нами:*\n\n"
        f"WhatsApp: +{settings.admin_whatsapp}\n"
        f"Или оформите заказ прямо через бота!",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
