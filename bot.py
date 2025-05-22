import os
import asyncpg
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime

BOT_TOKEN = "7548380199:AAGOJwrxWmzuZCEnloeSQ3NW0TbUJZgGvS4"
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

user_state = {}
user_data = {}

# ---------------- ИНИЦИАЛИЗАЦИЯ БД ----------------
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

# ---------------- КОМАНДА /START ----------------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("\ud83c\uddf7\ud83c\uddfa \u0420\u0443\u0441\u0441\u043a\u0438\u0439", callback_data="lang_ru"),
        InlineKeyboardButton("\ud83c\uddfa\ud83c\uddff O\u2018zbekcha", callback_data="lang_uz")
    )
    await message.answer("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u044f\u0437\u044b\u043a / Tilni tanlang:", reply_markup=keyboard)

# ---------------- УСТАНОВКА ЯЗЫКА ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = None
    await callback.message.edit_reply_markup()
    await send_main_menu(callback.message, lang)

# ---------------- ГЛАВНОЕ МЕНЮ ----------------
async def send_main_menu(message, lang):
    text = "\ud83d\udd3b \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:" if lang == "ru" else "\ud83d\udd3b Amalni tanlang:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        keyboard.add(KeyboardButton("\ud83d\udcdd \u041e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u044f\u0432\u043a\u0443"), KeyboardButton("\ud83d\udcca \u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u044f\u0432\u043a\u0438"))
        keyboard.add(KeyboardButton("\u2699\ufe0f \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438"))
    else:
        keyboard.add(KeyboardButton("\ud83d\udcdd Murojaat qoldirish"), KeyboardButton("\ud83d\udcca Murojaat holati"))
        keyboard.add(KeyboardButton("\u2699\ufe0f Sozlamalar"))
    await message.answer(text, reply_markup=keyboard)

# ---------------- ОБРАБОТЧИКИ КНОПОК ----------------
@dp.message_handler(lambda m: m.text in ["\ud83d\udcdd \u041e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0437\u0430\u044f\u0432\u043a\u0443", "\ud83d\udcdd Murojaat qoldirish"])
async def new_ticket(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = "city"
    prompt = "\ud83d\udccd \u0423\u043a\u0430\u0436\u0438\u0442\u0435 \u0432\u0430\u0448 \u0433\u043e\u0440\u043e\u0434:" if lang == "ru" else "\ud83d\udccd Shahringizni kiriting:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434"))
    await message.answer(prompt, reply_markup=keyboard)

@dp.message_handler(lambda m: m.text == "\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434")
async def go_back(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    user_state[user_id] = None
    await send_main_menu(message, lang)

# ---------------- ЭТАПЫ ----------------
@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "city")
async def ask_department(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["city"] = message.text
    user_state[user_id] = "department"
    lang = user_data[user_id]["lang"]
    text = "\ud83c\udfe2 \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043e\u0442\u0434\u0435\u043b:" if lang == "ru" else "\ud83c\udfe2 Bo\u2018limni tanlang:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434"))
    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
async def ask_problem(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["department"] = message.text
    user_state[user_id] = "problem"
    lang = user_data[user_id]["lang"]
    text = "\ud83d\udcdd \u041e\u043f\u0438\u0448\u0438\u0442\u0435 \u043f\u0440\u043e\u0431\u043b\u0435\u043c\u0443:" if lang == "ru" else "\ud83d\udcdd Muammoni batafsil yozing:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434"))
    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["message"] = message.text
    lang = user_data[user_id]["lang"]

    conn = await asyncpg.connect(DATABASE_URL)
    count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
    ticket_number = str(count + 1).zfill(5)

    await conn.execute('''
        INSERT INTO tickets (user_id, lang, city, department, message, ticket_number, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    ''', user_id, lang, user_data[user_id]["city"], user_data[user_id]["department"], user_data[user_id]["message"], ticket_number, "Новая")
    await conn.close()

    confirm = (
        f"✅ Ваше обращение зарегистрировано под номером №{ticket_number}" if lang == "ru"
        else f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi."
    )
    await message.answer(confirm, reply_markup=ReplyKeyboardRemove())
    user_state.pop(user_id, None)

    # Уведомление в группу
    admin_chat_id = -4680581564
    msg = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {'Русский' if lang == 'ru' else 'O‘zbekcha'}
📍 <b>Город:</b> {user_data[user_id]['city']}
🏢 <b>Отдел:</b> {user_data[user_id]['department']}
📝 <b>Сообщение:</b> {user_data[user_id]['message']}
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    await bot.send_message(admin_chat_id, msg, reply_markup=keyboard)

# ---------------- ОТВЕТ /reply 00001 текст ----------------
@dp.message_handler(lambda m: m.chat.id == -4680581564 and m.text.startswith("/reply"))
async def reply_to_user(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("⚠️ Формат: /reply 00001 ваш ответ")
        return

    ticket_number, reply_text = parts[1], parts[2]

    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT user_id, city, department, message, lang FROM tickets WHERE ticket_number = $1", ticket_number)
    if not row:
        await conn.close()
        await message.reply("❌ Тикет не найден.")
        return

    user_id = row["user_id"]
    city = row["city"]
    department = row["department"]
    question = row["message"]
    lang = row["lang"]

    # Отправляем пользователю ответ
    await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")
    await conn.execute("UPDATE tickets SET reply = $1 WHERE ticket_number = $2", reply_text, ticket_number)
    await conn.close()

    # Уведомление в группу — с кнопками и видимым ответом
    msg_text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {"Русский" if lang == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {city}
🏢 <b>Отдел:</b> {department}
📝 <b>Сообщение:</b> {question}

📬 <b>Ответ:</b> {reply_text}
    """.strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )

    await message.reply("✅ Ответ отправлен.")  # подтверждение админу
    await message.answer(msg_text, reply_markup=keyboard)

# ---------------- ИЗМЕНЕНИЕ СТАТУСА ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def update_status(callback: types.CallbackQuery):
    _, ticket_number, status = callback.data.split("|")
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE tickets SET status = $1 WHERE ticket_number = $2", status, ticket_number)
    await conn.close()
    await callback.answer(f"Статус обновлён: {status}")

# ---------------- ПОКАЗ ЗАЯВОК ----------------
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
        text += (
            f"<b>№{row['ticket_number']}</b> — {row['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"📌 Статус: <i>{row['status']}</i>\n"
            f"📝 {row['message'][:100]}\n\n"
        )
    await message.answer(text, parse_mode="HTML")

# ---------------- СТАРТ ----------------
async def main():
    await init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
