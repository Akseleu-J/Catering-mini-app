"""states.py — All FSM state groups."""

from aiogram.fsm.state import State, StatesGroup


class CheckoutFSM(StatesGroup):
    waiting_name     = State()   # Step 1: client name
    waiting_date     = State()   # Step 2: event date (DD.MM.YYYY)
    waiting_time     = State()   # Step 3: event time (HH:MM)
    waiting_location = State()   # Step 4: location / address
    confirming       = State()   # Step 5: confirm before submitting


class CartAddFSM(StatesGroup):
    choosing_mode    = State()   # Manual or per-person
    waiting_quantity = State()   # Manual quantity input
    waiting_guests   = State()   # Guest count for per-person calc


class ReviewFSM(StatesGroup):
    waiting_text     = State()   # Optional text after rating


class AdminCategoryFSM(StatesGroup):
    waiting_name     = State()
    waiting_emoji    = State()
    waiting_desc     = State()
    editing_name     = State()
    editing_emoji    = State()


class AdminProductFSM(StatesGroup):
    waiting_category    = State()
    waiting_name        = State()
    waiting_description = State()
    waiting_price       = State()
    waiting_photo       = State()
    waiting_serving     = State()
    editing_name        = State()
    editing_price       = State()
    editing_photo       = State()
    editing_description = State()


class AdminBroadcastFSM(StatesGroup):
    waiting_message  = State()
    confirming       = State()
