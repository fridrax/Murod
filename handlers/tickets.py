import asyncpg
import html
from datetime import datetime
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, bot
from config import DATABASE_URL, ADMIN_CHAT_ID
from keyboards import departments_keyboard, main_menu
from utils.state import user_data, user_state

# Обработка кнопки "Оставить заявку"/"Murojaat qoldirish"
@dp.message_handler(lambda m: m.text in ["📝 Оставить заявку", "📝 Murojaat qoldirish"])
async def create_ticket(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"lang": "ru", "city": None, "department": None, "message": None}
    else:
        user_data[user_id]["city"] = None
        user_data[user_id]["department"] = None
        user_data[user_id]["message"] = None

    user_state[user_id] = "city"
    lang = user_data[user_id]["lang"]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Назад"))
    await message.answer(
        "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:",
        reply_markup=kb
    )

# Обработка шага ввода города
@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "city")
async def ask_department(message: types.Message):
    user_id = message.from_user.id

    # Обработка кнопки Назад
    if message.text == "🔙 Назад":
        lang = user_data.get(user_id, {}).get("lang", "ru")
        user_state[user_id] = None
        await message.answer(
            "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:",
            reply_markup=main_menu(lang)
        )
        return

    user_data[user_id]["city"] = message.text.strip()
    user_state[user_id] = "department"
    lang = user_data[user_id]["lang"]

    text = (
        "🚩 Выберите отдел из списка или введите вручную:" if lang == "ru"
        else "🚩 Bo'limni tanlang yoki o'zingiz yozing:"
    )
    kb = departments_keyboard(lang)
    kb.add(KeyboardButton("🔙 Назад"))
    await message.answer(text, reply_markup=kb)

# Обработка шага ввода отдела
@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
async def ask_problem(message: types.Message):
    user_id = message.from_user.id

    # Обработка кнопки Назад
    if message.text == "🔙 Назад":
        user_state[user_id] = "city"
        lang = user_data[user_id]["lang"]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("🔙 Назад"))
        await message.answer(
            "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:",
            reply_markup=kb
        )
        return

    user_data[user_id]["department"] = message.text.strip()
    user_state[user_id] = "problem"
    lang = user_data[user_id]["lang"]

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Назад"))
    await message.answer(
        "📝 Опишите проблему:" if lang == "ru" else "📝 Muammoni tasvirlab bering:",
        reply_markup=kb
    )

# Обработка шага описания проблемы и САМОГО СОЗДАНИЯ ТИКЕТА
@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id

    # Обработка кнопки Назад
    if message.text == "🔙 Назад":
        user_state[user_id] = "department"
        lang = user_data[user_id]["lang"]
        kb = departments_keyboard(lang)
        kb.add(KeyboardButton("🔙 Назад"))
        text = (
            "🚩 Выберите отдел из списка или введите вручную:" if lang == "ru"
            else "🚩 Bo'limni tanlang yoki o'zingiz yozing:"
        )
        await message.answer(text, reply_markup=kb)
        return

    user_data[user_id]["message"] = message.text.strip()
    lang = user_data[user_id]["lang"]
    city = user_data[user_id]["city"]
    department = user_data[user_id]["department"]
    issue_text = user_data[user_id]["message"]
    created_at = datetime.now()

    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # Вставляем заявку и получаем id
        ticket_id = await conn.fetchval("""
            INSERT INTO tickets (user_id, lang, city, department, message, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, user_id, lang, city, department, issue_text, "Новая", created_at)
        ticket_number = str(ticket_id).zfill(5)
        await conn.execute(
            "UPDATE tickets SET ticket_number = $1 WHERE id = $2",
            ticket_number, ticket_id
        )
    except Exception as e:
        print("❌ Ошибка при сохранении заявки:", repr(e))
        await message.answer("❌ Ошибка при сохранении заявки." if lang == "ru" else "❌ Murojaatni saqlashda xatolik.")
        return
    finally:
        if conn:
            await conn.close()

    user_state[user_id] = None

    confirm = (
        f"✅ Ваше обращение зарегистрировано под номером №{ticket_number}"
        if lang == "ru" else
        f"✅ Murojaatingiz №{ticket_number} ro'yxatga olindi"
    )
    await message.answer(confirm)

    lang_name = "Русский" if lang == "ru" else "O‘zbekcha"
    msg = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {created_at.strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {lang_name}
📍 <b>Город:</b> {html.escape(city)}
🏢 <b>Отдел:</b> {html.escape(department)}
📝 <b>Сообщение:</b> {html.escape(issue_text)}
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )

    await bot.send_message(ADMIN_CHAT_ID, msg, reply_markup=keyboard)
