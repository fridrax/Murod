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
    try:
        async with asyncpg.connect(DATABASE_URL) as conn:
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
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz")
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)

# ---------------- УСТАНОВКА ЯЗЫКА ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Сохраняем язык и сбрасываем состояние
    user_data[user_id] = {
        "lang": lang,
        "city": None,
        "department": None,
        "message": None
    }
    user_state[user_id] = None

    # Удаляем кнопки выбора языка
    await callback.message.edit_reply_markup()

    # Ответ, чтобы убрать "часики"
    await callback.answer()

    # Показываем главное меню на выбранном языке
    await send_main_menu(callback.message, lang)

# ---------------- ГЛАВНОЕ МЕНЮ ----------------
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def send_main_menu(message, lang):
    text = "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    if lang == "ru":
        keyboard.add(
            KeyboardButton("📝 Оставить заявку"),
            KeyboardButton("📊 Статус заявки")
        )
        keyboard.add(KeyboardButton("⚙️ Настройки"))
    else:
        keyboard.add(
            KeyboardButton("📝 Murojaat qoldirish"),
            KeyboardButton("📊 Murojaat holati")
        )
        keyboard.add(KeyboardButton("⚙️ Sozlamalar"))

    await message.answer(text, reply_markup=keyboard)

# ---------------- ОБРАБОТЧИКИ КНОПОК ----------------

@dp.message_handler(lambda m: m.text in ["📝 Оставить заявку", "📝 Murojaat qoldirish"])
async def new_ticket(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")

    # Обновим user_data, если оно не полное
    user_data[user_id] = {
        "lang": lang,
        "city": None,
        "department": None,
        "message": None
    }

    user_state[user_id] = "city"

    prompt = "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("◀️ Назад"))
    await message.answer(prompt, reply_markup=keyboard)


@dp.message_handler(lambda m: m.text == "◀️ Назад")
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

    text = "🏢 Выберите отдел:" if lang == "ru" else "🏢 Bo‘limni tanlang:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("◀️ Назад"))
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
async def ask_problem(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["department"] = message.text
    user_state[user_id] = "problem"
    lang = user_data[user_id]["lang"]

    text = "📝 Опишите проблему:" if lang == "ru" else "📝 Muammoni batafsil yozing:"
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("◀️ Назад"))
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["message"] = message.text
    lang = user_data[user_id]["lang"]

    # Сохраняем заявку
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
        ticket_number = str(count + 1).zfill(5)

        await conn.execute('''
            INSERT INTO tickets (user_id, lang, city, department, message, ticket_number, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', user_id, lang, user_data[user_id]["city"], user_data[user_id]["department"], user_data[user_id]["message"], ticket_number, "Новая")
        await conn.close()
    except Exception as e:
        await message.answer("❌ Ошибка при сохранении заявки." if lang == "ru" else "❌ Murojaatni saqlashda xatolik yuz berdi.")
        print("Ошибка сохранения в БД:", e)
        return

    # Подтверждение
    confirm = (
        f"✅ Ваше обращение зарегистрировано под номером №{ticket_number}" if lang == "ru"
        else f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi."
    )
    await message.answer(confirm, reply_markup=ReplyKeyboardRemove())

    # Очистка состояния
    user_state.pop(user_id, None)

    # ---------------- УВЕДОМЛЕНИЕ В ГРУППУ ----------------
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import html

admin_chat_id = -4680581564

# Экранируем текст, чтобы избежать ошибок от HTML
city = html.escape(user_data[user_id]['city'])
department = html.escape(user_data[user_id]['department'])
user_message = html.escape(user_data[user_id]['message'])

msg = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {'Русский' if lang == 'ru' else 'O‘zbekcha'}
📍 <b>Город:</b> {city}
🏢 <b>Отдел:</b> {department}
📝 <b>Сообщение:</b> {user_message}
""".strip()

keyboard = InlineKeyboardMarkup(row_width=2)
keyboard.add(
    InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
    InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
    InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
    InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
)

await bot.send_message(admin_chat_id, msg, reply_markup=keyboard)

@dp.message_handler(lambda m: m.chat.id == -4680581564 and m.text.startswith("/reply"))
async def reply_to_user(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("⚠️ Формат: /reply 00001 ваш ответ")
        return

    ticket_number, reply_text = parts[1], parts[2]

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow(
            "SELECT user_id, city, department, message, lang FROM tickets WHERE ticket_number = $1",
            ticket_number
        )

        if not row:
            await message.reply("❌ Тикет не найден.")
            return

        user_id = row["user_id"]
        city = html.escape(row["city"])
        department = html.escape(row["department"])
        question = html.escape(row["message"])
        lang = row["lang"]
        reply_clean = html.escape(reply_text)

        # Ответ пользователю
        await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")

        # Обновление БД
        await conn.execute("UPDATE tickets SET reply = $1 WHERE ticket_number = $2", reply_text, ticket_number)
        await conn.close()

        # Подтверждение админу
        await message.reply("✅ Ответ отправлен.")

        # Обновлённое сообщение
        msg_text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {"Русский" if lang == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {city}
🏢 <b>Отдел:</b> {department}
📝 <b>Сообщение:</b> {question}

📬 <b>Ответ:</b> {reply_clean}
""".strip()

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
            InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
            InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
            InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
        )

        await bot.send_message(message.chat.id, msg_text, reply_markup=keyboard)

    except Exception as e:
        await message.reply("❌ Ошибка при ответе.")
        print("Ошибка в /reply:", e)

@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def update_status(callback: types.CallbackQuery):
    try:
        _, ticket_number, status = callback.data.split("|")

        # Обновление статуса в базе данных
        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("SELECT id FROM tickets WHERE ticket_number = $1", ticket_number)
        if not row:
            await callback.answer("❌ Тикет не найден.")
            await conn.close()
            return

        await conn.execute("UPDATE tickets SET status = $1 WHERE ticket_number = $2", status, ticket_number)
        await conn.close()

        # Подтверждение
        await callback.answer(f"✅ Статус обновлён: {status}")

    except Exception as e:
        print("Ошибка при обновлении статуса:", e)
        await callback.answer("❌ Ошибка при обновлении статуса.")

@dp.message_handler(lambda m: m.text in ["📋 Статус заявки", "📊 Murojaat holati"])
async def show_status(message: types.Message):
    await show_user_tickets(message)


async def show_user_tickets(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch(
            "SELECT * FROM tickets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10",
            user_id
        )
        await conn.close()
    except Exception as e:
        print("Ошибка при получении заявок:", e)
        await message.answer("❌ Ошибка при загрузке заявок." if lang == "ru" else "❌ So'rovlarni yuklashda xatolik.")
        return

    if not rows:
        await message.answer(
            "❗️ У вас пока нет заявок." if lang == "ru" else "❗️ Sizda hali hech qanday murojaat yo'q."
        )
        return

    text = "🗂 <b>Последние заявки:</b>\n\n" if lang == "ru" else "🗂 <b>So‘nggi murojaatlar:</b>\n\n"

    for row in rows:
        msg = html.escape(row["message"])
        status = html.escape(row["status"])
        created = row["created_at"].strftime("%Y-%m-%d %H:%M")
        text += (
            f"<b>№{row['ticket_number']}</b> — {created}\n"
            f"📌 Статус: <i>{status}</i>\n"
            f"📝 {msg[:100]}...\n\n"
        )

    await message.answer(text, parse_mode="HTML")

# ---------------- СТАРТ ----------------
async def main():
    await init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
