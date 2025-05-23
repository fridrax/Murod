from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import dp, bot
from keyboards import departments_keyboard
from handlers.start import user_data, user_state
import sqlite3, datetime

@dp.message_handler(lambda m: m.text in ["📝 Оставить заявку", "📝 Murojaat jo'natish"])
async def create_ticket(message: types.Message):
    """Handler for the 'Create Ticket' action from the main menu."""
    user_id = message.from_user.id
    # Ensure user has a data record (carry over language or set default)
    if user_id not in user_data:
        user_data[user_id] = {"lang": "ru", "city": None, "department": None, "message": None}
    else:
        # Reset any previous ticket info for a fresh submission
        user_data[user_id]["city"] = None
        user_data[user_id]["department"] = None
        user_data[user_id]["message"] = None

    # Set the conversation state to expect the city next
    user_state[user_id] = "city"
    lang = user_data[user_id]["lang"]

    # Prepare a reply keyboard with a "Back" button for cancellation
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Назад"))
    # Ask the user for their city
    await message.answer(
        "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:",
        reply_markup=kb
    )

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "city")
async def ask_department(message: types.Message):
    """Handles the user response for city and asks for department."""
    user_id = message.from_user.id
    # Save the city provided by the user
    user_data[user_id]["city"] = message.text.strip()
    # Set state to expect department next
    user_state[user_id] = "department"
    lang = user_data[user_id]["lang"]

    # Prompt text for department selection, with support for manual entry
    text = (
        "🚩 Выберите отдел из списка или введите вручную:" if lang == "ru"
        else "🚩 Bo'limni tanlang yoki o'zingiz yozing:"
    )
    # Show available departments (as reply keyboard) and allow manual input
    await message.answer(text, reply_markup=departments_keyboard(lang))

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
async def ask_problem(message: types.Message):
    """Handles the user response for department and asks for problem description."""
    user_id = message.from_user.id
    # Save the department chosen or entered by the user
    user_data[user_id]["department"] = message.text.strip()
    # Set state to expect the problem description next
    user_state[user_id] = "problem"
    lang = user_data[user_id]["lang"]

    # Prepare a reply keyboard with a "Back" button for cancellation
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Назад"))
    # Ask the user to describe the problem
    await message.answer(
        "📝 Опишите проблему:" if lang == "ru" else "📝 Muammoni tasvirlab bering:",
        reply_markup=kb
    )

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    """Final step: saves the ticket and notifies the user and admin."""
    user_id = message.from_user.id
    # Save the problem description
    user_data[user_id]["message"] = message.text.strip()
    lang = user_data[user_id]["lang"]
    city = user_data[user_id]["city"]
    department = user_data[user_id]["department"]
    issue_text = user_data[user_id]["message"]

    # Insert the new ticket into the database
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tickets (user_id, lang, city, department, message, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, lang, city, department, issue_text, "Новая", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    ticket_id = cur.lastrowid  # ID of the newly created ticket
    conn.close()

    # Mark this conversation flow as finished
    user_state[user_id] = None

    # Notify the user about successful submission
    ticket_no = f"{ticket_id:05d}"  # Format ticket number with leading zeros (e.g., 00030)
    if lang == "ru":
        await message.answer(f"✅ Ваше обращение зарегистрировано под номером №{ticket_no}")
    else:
        await message.answer(f"✅ Murojaatingiz №{ticket_no} ro‘yxatga olindi")

    # Prepare and send a notification to the admin group with ticket details
    from data.config import ADMIN_GROUP_ID  # The chat ID of the admin group (set in config)
    lang_name = "Русский" if lang == "ru" else "Узбекский"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    admin_text = (
        "Новая заявка 📝\n"
        f"Дата: {timestamp}\n"
        f"Номер: №{ticket_no}\n"
        f"Язык: {lang_name}\n"
        f"Город: {city}\n"
        f"Отдел: {department}\n"
        f"Сообщение: {issue_text}\n\n"
        f"👉 Для ответа используйте команду: /reply {ticket_no} <текст ответа>"
    )
    # (Optional) Inline keyboard for admin actions (e.g., Reply, In Progress, Done, Reject)
    # from keyboards import admin_reply_keyboard
    # admin_kb = admin_reply_keyboard(ticket_id)
    # Send the message to the admin group
    await bot.send_message(ADMIN_GROUP_ID, admin_text)  # , reply_markup=admin_kb if using inline buttons
