from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = "7548380199:AAF2yqncpxlTZeBekP3heA8b_N23oNGEmNw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_lang = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang_uz")
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_lang[user_id] = lang

    if lang == "ru":
        text = "Добро пожаловать в SG Hotline! Вы можете анонимно отправить обращение."
    else:
        text = "SG Hotline ga xush kelibsiz! Siz bu yerda anonim murojaat yuborishingiz mumkin."

    await callback.message.edit_reply_markup()
    await callback.message.answer(text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
