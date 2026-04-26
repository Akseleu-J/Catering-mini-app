"""handlers/menu.py — Menu catalog with pagination. Fixed filters."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import CategoryRepository, ProductRepository
from keyboards.user_kb import (
    categories_kb, products_kb, product_detail_kb,
    add_to_cart_mode_kb,
)
from utils.formatters import fmt_product_card
from config import settings

router = Router()


@router.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery, session: AsyncSession):
    repo = CategoryRepository(session)
    categories = await repo.get_active()
    if not categories:
        await callback.answer("Меню пока пустое 😔", show_alert=True)
        return
    try:
        await callback.message.edit_text(
            "📋 *Выберите категорию:*",
            parse_mode="Markdown",
            reply_markup=categories_kb(categories),
        )
    except Exception:
        await callback.message.answer(
            "📋 *Выберите категорию:*",
            parse_mode="Markdown",
            reply_markup=categories_kb(categories),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: CallbackQuery, session: AsyncSession):
    parts  = callback.data.split("_")
    cat_id = int(parts[1])
    page   = int(parts[3]) if len(parts) >= 4 and parts[2] == "page" else 0
    await _show_category_page(callback, session, cat_id, page)


async def _show_category_page(callback, session, cat_id, page):
    per_page = settings.items_per_page
    repo     = ProductRepository(session)
    products = await repo.get_by_category(
        cat_id, available_only=True,
        offset=page * per_page, limit=per_page,
    )
    total = await repo.count_by_category(cat_id)

    if not products:
        await callback.answer("В этой категории нет доступных позиций.", show_alert=True)
        return

    cat  = await CategoryRepository(session).get_by_id(cat_id)
    text = f"{cat.emoji} *{cat.name}*\n\nВыберите блюдо:"
    kb   = products_kb(products, cat_id, page, total, per_page)

    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def cb_product_detail(callback: CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split("_")[1])
    product    = await ProductRepository(session).get_by_id(product_id)

    if not product:
        await callback.answer("Продукт не найден!", show_alert=True)
        return

    text = fmt_product_card(product)
    kb   = product_detail_kb(product.id, product.category_id)

    if product.photo_file_id:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=product.photo_file_id,
            caption=text, parse_mode="Markdown", reply_markup=kb,
        )
    else:
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def cb_add_to_cart_start(callback: CallbackQuery):
    """Show calculation mode: manual qty OR per person.
    Handles only 'add_<id>' — skips 'add_manual_*' and 'add_guests_*'."""
    parts = callback.data.split("_")
    if len(parts) != 2:
        return  # add_manual_* or add_guests_* handled in cart.py

    product_id = int(parts[1])
    text = (
        "🛒 *Как добавить в корзину?*\n\n"
        "✏️ *Вручную* — введите количество порций\n"
        "👥 *По гостям* — бот рассчитает автоматически\n\n"
        "_(1 порция рассчитана на определённое кол-во гостей)_"
    )
    try:
        await callback.message.edit_text(
            text, parse_mode="Markdown",
            reply_markup=add_to_cart_mode_kb(product_id),
        )
    except Exception:
        try:
            await callback.message.edit_caption(
                caption=text, parse_mode="Markdown",
                reply_markup=add_to_cart_mode_kb(product_id),
            )
        except Exception:
            await callback.message.answer(
                text, parse_mode="Markdown",
                reply_markup=add_to_cart_mode_kb(product_id),
            )
    await callback.answer()
