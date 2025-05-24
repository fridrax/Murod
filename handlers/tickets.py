from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import bot, dp
from utils.state import user_state, user_data
from database.db import DATABASE_URL
import asyncpg
from datetime import datetime
import os

def register_tickets(dp):
    @dp.message_handler(lambda m: m.text in ["📝 Оставить заявку", "📝 Murojaat qoldirish"])
    async def new_ticket(message: types.Message):
        user_id = message.from_user.id
        lang = user_data.get(user_id, {}).get("lang", "ru")
        user_data[user_id] = {"lang": lang}
        user_state[user_id] = "city"
        prompt = "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:"
        await message.answer(prompt)

    @dp.message_handler(lambda m: user_state.get(m.from_user.id) == "city")
    async def get_department(message: types.Message):
        user_id = message.from_user.id
        user_data[user_id]["city"] = message.text
        user_state[user_id] = "department"
        lang = user_data[user_id]["lang"]
        await message.answer("🏢 Выберите отдел:" if lang == "ru" else "🏢 Bo‘limni tanlang:")

    @dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
    async def get_problem(message: types.Message):
        user_id = message.from_user.id
        user_data[user_id]["department"] = message.text
        user_state[user_id] = "problem"
        lang = user_data[user_id]["lang"]
        await message.answer("📝 Опишите проблему:" if lang == "ru" else "📝 Muammoni batafsil yozing:")

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
            f"✅ Ваше обращение зарегистрировано под номером №{ticket_number}"
            if lang == "ru" else
            f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi."
        )
        await message.answer(confirm)
        user_state.pop(user_id, None)

        # Уведомление в группу
        admin_chat_id = int(os.getenv("ADMIN_CHAT_ID", "-4680581564"))
        text = f"""
    📨 <b>Новая заявка</b>
    🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
    🎫 <b>Номер:</b> №{ticket_number}
    🌐 <b>Язык:</b> {"Русский" if lang == "ru" else "O‘zbekcha"}
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
        await bot.send_message(admin_chat_id, text, reply_markup=keyboard)

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
