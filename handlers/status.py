import os
import asyncpg
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from datetime import datetime

BOT_TOKEN = "7548380199:AAELReJVgsiBN-i5a4jjJQQLT7x2aNgir8Q"
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_state = {}
user_data = {}

def register_handlers(dp: Dispatcher):
    @dp.message_handler(lambda m: m.text in ["📊 Статус заявки", "📊 Murojaat holati"])
    async def show_status(message: types.Message):
        user_id = message.from_user.id

        # Для теста — если нет языка, ставим по умолчанию русский
        if user_id not in user_data:
            user_data[user_id] = {"lang": "ru"}
        lang = user_data[user_id]["lang"]

        conn = None
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            rows = await conn.fetch(
                "SELECT ticket_number, status FROM tickets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10",
                user_id
            )
        except Exception as e:
            print("❌ Ошибка при получении заявок:", e)
            await message.answer("❌ Ошибка при загрузке заявок." if lang == "ru" else "❌ So‘rovlarni yuklashda xatolik.")
            return
        finally:
            if conn:
                await conn.close()

        if not rows:
            await message.answer("❗️ У вас пока нет заявок." if lang == "ru" else "❗️ Sizda hali hech qanday murojaat yo'q.")
            return

        header = "📋 <b>Список ваших заявок:</b>\n\n" if lang == "ru" else "📋 <b>Murojaatlaringiz ro‘yxati:</b>\n\n"
        body = ""
        for row in rows:
            number = html.escape(row["ticket_number"])
            status = html.escape(row["status"])
            body += f"🎫 <b>№{number}</b> — <i>{status}</i>\n"

        await message.answer(header + body, parse_mode="HTML")
