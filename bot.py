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
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    await conn.close()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_uz")
    )
    await message.answer("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a / Tilni tanlang:", reply_markup=keyboard)

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

@dp.message_handler(commands=["mytickets"])
async def show_user_tickets(message: types.Message):
    user_id = message.from_user.id

    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("""
        SELECT ticket_number, created_at, message, status
        FROM tickets
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 10
    """, user_id)
    await conn.close()

    if not rows:
        await message.answer("❗️У вас пока нет обращений.")
        return

    text = "🗃 <b>Ваши последние обращения:</b>\n\n"
    for row in rows:
        msg_preview = row["message"][:100]
        text += (
            f"<b>{row['ticket_number']}</b> — {row['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"📝 {msg_preview}\n"
            f"📌 Статус: <i>{row['status']}</i>\n\n"
        )

    await message.answer(text.strip(), parse_mode="HTML")

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["message"] = message.text
    lang = user_data[user_id]["lang"]

    # Генерация номера тикета (только цифры)
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT COUNT(*) FROM tickets")
    count = row["count"]
    ticket_number = str(count + 1).zfill(5)  # '00015'

    await conn.execute('''
        INSERT INTO tickets (user_id, lang, city, department, message, ticket_number, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    ''', user_id, lang, user_data[user_id]["city"], user_data[user_id]["department"], user_data[user_id]["message"], ticket_number, "Новая")
    await conn.close()

    # Сообщение пользователю
    confirm = (
        f"✅ Ваше обращение зарегистрировано под номером №{ticket_number}"
        if lang == "ru" else
        f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi."
    )
    await message.answer(confirm)
    user_state.pop(user_id, None)

    # Отправка в Telegram-группу
    admin_chat_id = -4680581564

    msg = f"""
📨 <b>Новое обращение!</b>
📅 <b>Дата:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {"Русский" if lang == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {user_data[user_id]["city"]}
🏢 <b>Отдел:</b> {user_data[user_id]["department"]}
📝 <b>Сообщение:</b> {user_data[user_id]["message"]}
    """.strip()

    reply_keyboard = InlineKeyboardMarkup()
    reply_keyboard.add(
        InlineKeyboardButton(
            text="✉️ Ответить",
            switch_inline_query_current_chat=f"/reply {ticket_number}"
        )
    )

    await bot.send_message(admin_chat_id, msg, parse_mode="HTML", reply_markup=reply_keyboard)

    status_buttons = InlineKeyboardMarkup(row_width=3)
    status_buttons.add(
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    await bot.send_message(admin_chat_id, f"✏️ Выберите новый статус для заявки №{ticket_number}:", reply_markup=status_buttons)

    user_data.pop(user_id, None)

@dp.message_handler(lambda m: m.chat.id == -4680581564 and "/reply" in m.text)
async def handle_admin_reply(message: types.Message):
    try:
        # Убираем @username, если он есть
        text = message.text.replace(f"@{(await bot.get_me()).username}", "").strip()

        parts = text.split(" ", 2)
        if len(parts) < 3:
            await message.reply("⚠️ Неверный формат. Используйте: /reply 00015 ваш текст")
            return

        ticket_input = parts[1].replace("№", "").strip().zfill(5)
        ticket_number = ticket_input
        reply_text = parts[2]

        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("SELECT user_id FROM tickets WHERE ticket_number = $1", ticket_number)
        await conn.close()

        if not row:
            await message.reply("❌ Тикет не найден.")
            return

        user_id = row["user_id"]
        await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")
        await message.reply("✅ Ответ отправлен.")

    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")
        print("‼️ Ошибка:", e)

@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def handle_status_change(callback: types.CallbackQuery):
    _, ticket_number, new_status = callback.data.split("|")

    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE tickets SET status = $1 WHERE ticket_number = $2", new_status, ticket_number)
    await conn.close()

    await callback.answer()
    await callback.message.edit_reply_markup()
    await callback.message.answer(f"✅ Статус заявки <b>{ticket_number}</b> обновлён на <b>{new_status}</b>", parse_mode="HTML")

async def main():
    await init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
