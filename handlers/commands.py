from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config.settings import dp
from utils.state import user_state, user_data

def register_commands(dp):
    @dp.message_handler(commands=["start"])
    async def start(message: types.Message):
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz")
        )
        await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)

    @dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
    async def set_language(callback: types.CallbackQuery):
        lang = callback.data.split("_")[1]
        user_id = callback.from_user.id
        user_data[user_id] = {"lang": lang}
        user_state[user_id] = None

        await callback.message.edit_reply_markup()

        menu_text = "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:"
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        if lang == "ru":
            menu.add(KeyboardButton("📝 Оставить заявку"), KeyboardButton("📋 Статус заявки"))
            menu.add(KeyboardButton("⚙️ Настройки"))
        else:
            menu.add(KeyboardButton("📝 Murojaat qoldirish"), KeyboardButton("📊 Murojaat holati"))
            menu.add(KeyboardButton("⚙️ Sozlamalar"))
        await callback.message.answer(menu_text, reply_markup=menu)
