import asyncpg
import html
from datetime import datetime
from loader import dp, bot
from config import DATABASE_URL
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Ответ на тикет в группе
@dp.message_handler(lambda m: m.chat.type in ["group", "supergroup"] and m.text.startswith("/reply"))
async def reply_to_user(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("⚠️ Формат: /reply 00001 ваш ответ")
        return

    ticket_number, reply_text = str(parts[1]), parts[2]
    conn = None

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

        await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")
        await conn.execute(
            "UPDATE tickets SET reply = $1 WHERE ticket_number = $2",
            reply_text,
            ticket_number
        )

        await message.reply("✅ Ответ отправлен.")

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
        print("Ошибка в /reply:", e)
        await message.reply("❌ Ошибка при ответе.")
    finally:
        if conn:
            await conn.close()

# Обработка кнопок статуса
@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def update_status(callback: types.CallbackQuery):
    conn = None
    try:
        _, ticket_number, status = callback.data.split("|")

        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("SELECT id FROM tickets WHERE ticket_number = $1", ticket_number)
        if not row:
            await callback.answer("❌ Тикет не найден.")
            return

        await conn.execute(
            "UPDATE tickets SET status = $1 WHERE ticket_number = $2",
            status,
            ticket_number
        )

        await callback.answer(f"✅ Статус обновлён: {status}")

    except Exception as e:
        print("Ошибка при обновлении статуса:", e)
        await callback.answer("❌ Ошибка при обновлении статуса.")
    finally:
        if conn:
            await conn.close()
