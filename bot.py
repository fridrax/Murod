import os
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from datetime import datetime

BOT_TOKEN = "7548380199:AAF2yqncpxlTZeBekP3heA8b_N23oNGEmNw"
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_state = {}  # user_id: step
user_data = {}   # user_id: dict with lang, city, department, message

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            lang TEXT,
            city TEXT,
            department TEXT,
            message TEXT,
            ticket_number TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    await conn.close()

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
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = "city"

    await callback.message.edit_reply_markup()
    text = "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:"
    await callback.message.answer(text)

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "city")
async def ask_department(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["city"] = message.text
    user_state[user_id] = "department"

    lang = user_data[user_id]["lang"]
    text = "🏢 Выберите отдел или введите вручную:" if lang == "ru" else "🏢 Bo‘limni tanlang yoki yozing:"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Отдел -1"), KeyboardButton("Отдел -2"), KeyboardButton("Отдел -3"))
    keyboard.add(KeyboardButton("✍️ Ввести вручную" if lang == "ru" else "✍️ Qo‘lda kiritish"))

    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "department")
async def ask_problem(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = "problem"
    user_data[user_id]["department"] = message.text
    lang = user_data[user_id]["lang"]
    text = "📝 Подробно опишите проблему:" if lang == "ru" else "📝 Muammoni batafsil yozing:"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["message"] = message.text
    lang = user_data[user_id]["lang"]

    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT COUNT(*) FROM tickets")
    count = row["count"]
    ticket_number = f"#{str(count + 1).zfill(5)}"

    await conn.execute('''
        INSERT INTO tickets (user_id, lang, city, department, message, ticket_number)
        VALUES ($1, $2, $3, $4, $5, $6)
    ''', user_id, lang, user_data[user_id]["city"], user_data[user_id]["department"], user_data[user_id]["message"], ticket_number)
    await conn.close()

    confirm = f"✅ Ваше обращение зарегистрировано под номером {ticket_number}" if lang == "ru" else f"✅ Murojaatingiz {ticket_number} raqam bilan ro'yxatga olindi."
    await message.answer(confirm)

    user_state.pop(user_id, None)
    user_data.pop(user_id, None)

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)
