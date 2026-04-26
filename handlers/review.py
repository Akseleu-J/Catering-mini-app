"""handlers/review.py — Post-event review collection. Fixed filters."""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.order_repo import ReviewRepository
from keyboards.user_kb import review_text_kb, cancel_kb, main_menu_kb
from states import ReviewFSM
from config import get_logger

logger = get_logger(__name__)
router = Router()


@router.callback_query(F.data.startswith("review_"))
async def cb_review_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = callback.data  # e.g. review_5_3 or review_skip_5 or review_done_5
    parts = data.split("_")

    # review_skip_<order_id>
    if parts[1] == "skip":
        order_id = int(parts[2])
        repo     = ReviewRepository(session)
        review   = await repo.get_by_order(order_id)
        if not review:
            await repo.create_for_order(order_id, callback.from_user.id)
        try:
            await callback.message.edit_text(
                "✅ Хорошо, пропускаем. Спасибо за использование нашего сервиса!",
                reply_markup=main_menu_kb(),
            )
        except Exception:
            await callback.message.answer("✅ Хорошо, пропускаем!", reply_markup=main_menu_kb())
        await callback.answer()
        return

    # review_done_<order_id>
    if parts[1] == "done":
        await state.clear()
        try:
            await callback.message.edit_text("✅ *Спасибо за отзыв!* 🙏", parse_mode="Markdown", reply_markup=main_menu_kb())
        except Exception:
            await callback.message.answer("✅ Спасибо!", reply_markup=main_menu_kb())
        await callback.answer()
        return

    # review_<order_id>_<rating>
    order_id = int(parts[1])
    rating   = int(parts[2])

    repo   = ReviewRepository(session)
    review = await repo.get_by_order(order_id)
    if not review:
        review = await repo.create_for_order(order_id, callback.from_user.id)

    await repo.submit(review.id, rating, None)
    await state.set_state(ReviewFSM.waiting_text)
    await state.update_data(review_id=review.id)

    stars = "⭐" * rating
    try:
        await callback.message.edit_text(
            f"{stars} Спасибо за оценку!\n\n"
            "💬 Хотите оставить комментарий? Напишите его или нажмите «Пропустить».",
            reply_markup=review_text_kb(order_id),
        )
    except Exception:
        await callback.message.answer(
            f"{stars} Спасибо! Напишите комментарий или нажмите «Пропустить».",
            reply_markup=review_text_kb(order_id),
        )
    await callback.answer()


@router.message(ReviewFSM.waiting_text)
async def msg_review_text(message: Message, state: FSMContext, session: AsyncSession):
    data   = await state.get_data()
    repo   = ReviewRepository(session)
    review = await repo.get_by_id(data["review_id"])
    if review:
        review.text = message.text
        review.review_created_at = datetime.utcnow()
    await state.clear()
    await message.answer(
        "✅ *Спасибо за отзыв!* Мы ценим ваше мнение 🙏",
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )
    logger.info(f"Review submitted by user {message.from_user.id}")
