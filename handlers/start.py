from aiogram import types
from aiogram.types import CallbackQuery
from loader import dp
from keyboards import lang_keyboard, main_menu
from utils.state import user_data, user_state  # ← Вынесено сюда

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    if message.chat.type != "private":
        return  # Игнорируем команду в групповых чатах

    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=lang_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    user_data[user_id] = {
        "lang": lang,
        "city": None,
        "department": None,
        "message": None
    }
    user_state[user_id] = None

    await callback.message.edit_reply_markup()
    await callback.answer()

    await callback.message.answer(
        "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:",
        reply_markup=main_menu(lang)
    )

@dp.message_handler(lambda m: m.text in ["📊 Статус заявки", "📊 Murojaat holati"])
async def handle_status_request(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data or "lang" not in user_data[user_id]:
    await message.answer("Пожалуйста, выберите язык / Iltimos, tilni tanlang:", reply_markup=lang_keyboard())
    return

    from handlers.status import show_status
    await show_status(message)
