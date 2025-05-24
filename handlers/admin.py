from aiogram import types
from config.settings import bot, dp
from database.db import DATABASE_URL
import asyncpg

def register_admin(dp):
    @dp.message_handler(lambda m: m.chat.id == -4680581564 and m.text.startswith("/reply"))
    async def reply_user(message: types.Message):
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            await message.reply("⚠️ Формат: /reply 00001 текст")
            return
        ticket_number, reply_text = parts[1], parts[2]

        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("SELECT user_id FROM tickets WHERE ticket_number = $1", ticket_number)
        if not row:
            await message.reply("❌ Тикет не найден.")
            await conn.close()
            return
        user_id = row["user_id"]
        await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")
        await conn.execute("UPDATE tickets SET reply = $1 WHERE ticket_number = $2", reply_text, ticket_number)
        await conn.close()
        await message.reply("✅ Ответ отправлен.")

    @dp.callback_query_handler(lambda c: c.data.startswith("status|"))
    async def update_status(callback: types.CallbackQuery):
        _, ticket_number, status = callback.data.split("|")
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("UPDATE tickets SET status = $1 WHERE ticket_number = $2", status, ticket_number)
        await conn.close()
        await callback.answer(f"Статус обновлён: {status}")
