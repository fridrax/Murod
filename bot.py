import os
import asyncpg
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from datetime import datetime

BOT_TOKEN = "7548380199:AAGOJwrxWmzuZCEnloeSQ3NW0TbUJZgGvS4"
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_state = {}
user_data = {}

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
            status TEXT,
            reply TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    await conn.close()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🇷🇸 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_uz")
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = None

    await callback.message.edit_reply_markup()

    text = "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        keyboard.add(KeyboardButton("📝 Оставить заявку"), KeyboardButton("📊 Статус заявки"))
        keyboard.add(KeyboardButton("⚙️ Настройки"))
    else:
        keyboard.add(KeyboardButton("📝 Murojaat qoldirish"), KeyboardButton("📊 Murojaat holati"))
        keyboard.add(KeyboardButton("⚙️ Sozlamalar"))
    await callback.message.answer(text, reply_markup=keyboard)

@dp.message_handler(lambda m: m.text in [
    "📝 Оставить заявку", 
    "📝 Murojaat qoldirish"])
async def new_ticket(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = "city"
    text = "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:"
    await message.answer(text)

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "city")
async def ask_department(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["city"] = message.text
    user_state[user_id] = "department"
    lang = user_data[user_id]["lang"]
    text = "🏢 Выберите отдел:" if lang == "ru" else "🏢 Bo‘limni tanlang:"
    await message.answer(text)

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "department")
async def ask_problem(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = "problem"
    user_data[user_id]["department"] = message.text
    lang = user_data[user_id]["lang"]
    text = "📝 Опишите проблему:" if lang == "ru" else "📝 Muammoni batafsil yozing:"
    await message.answer(text)

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["message"] = message.text
    lang = user_data[user_id]["lang"]

    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT COUNT(*) FROM tickets")
    count = row["count"]
    ticket_number = str(count + 1).zfill(5)

    await conn.execute('''
        INSERT INTO tickets (user_id, lang, city, department, message, ticket_number, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    ''', user_id, lang, user_data[user_id]["city"], user_data[user_id]["department"], user_data[user_id]["message"], ticket_number, "Новая")
    await conn.close()

    confirm = (
        f"✅ Ваше обращение регистрировано под номером №{ticket_number}" if lang == "ru"
        else f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi."
    )
    await message.answer(confirm)
    user_state.pop(user_id, None)

    # Сообщение в группу с кнопками
    admin_chat_id = -4680581564
    msg_text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {"Русский" if lang == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {user_data[user_id]['city']}
🏢 <b>Отдел:</b> {user_data[user_id]['department']}
📝 <b>Сообщение:</b> {user_data[user_id]['message']}
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    await bot.send_message(admin_chat_id, msg_text.strip(), parse_mode="HTML", reply_markup=keyboard)

@dp.message_handler(lambda m: m.chat.id == -4680581564 and m.text.startswith("/reply"))
async def reply_to_user(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("⚠️ Формат: /reply 00001 ваш ответ")
        return
    ticket_number, reply_text = parts[1], parts[2]

    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT user_id FROM tickets WHERE ticket_number = $1", ticket_number)
    if not row:
        await conn.close()
        await message.reply("❌ Тикет не найден.")
        return
    user_id = row["user_id"]
    await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:

{reply_text}")
    await conn.execute("UPDATE tickets SET reply = $1 WHERE ticket_number = $2", reply_text, ticket_number)
    await conn.close()
    await message.reply("✅ Ответ отправлен.")

@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def handle_status(callback: types.CallbackQuery):
    _, ticket_number, status = callback.data.split("|")
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE tickets SET status = $1 WHERE ticket_number = $2", status, ticket_number)
    await conn.close()
    await callback.answer(f"Статус обновлён: {status}")

@dp.message_handler(lambda m: m.text in ["📋 Статус заявки", "📊 Murojaat holati"])
async def show_status(message: types.Message):
    await show_user_tickets(message)

async def show_user_tickets(message: types.Message):
    user_id = message.from_user.id
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM tickets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10", user_id)
    await conn.close()

    if not rows:
        await message.answer("❗️ У вас пока нет заявок.")
        return

    text = "🗂 <b>Последние заявки:</b>\n\n"
    for row in rows:
        text += (f"<b>№{row['ticket_number']}</b> — {row['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                 f"📌 Статус: <i>{row['status']}</i>\n"
                 f"📝 {row['message'][:100]}\n\n")
    await message.answer(text, parse_mode="HTML")

async def main():
    await init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
