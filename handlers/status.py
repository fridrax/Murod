import asyncpg
import html
from loader import dp
from config import DATABASE_URL
from aiogram import types
from handlers.start import user_data

@dp.message_handler(lambda m: m.text in ["📋 Статус заявки", "📊 Murojaat holati"])
async def show_status(message: types.Message):
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
        await message.answer("❗️ У вас пока нет заявок." if lang == "ru" else "❗️ Sizda hali hech qanday murojaat yo'q.")
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
