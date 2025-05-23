from aiogram import types
from loader import dp
from utils.state import user_data  # переносим из start

@dp.message_handler(lambda m: m.text in ["⚙️ Настройки", "⚙️ Sozlamalar"])
async def settings_handler(message: types.Message):
    lang = user_data.get(message.from_user.id, {}).get("lang", "ru")
    text = "🛠 Раздел в разработке." if lang == "ru" else "🛠 Bo‘lim ishlab chiqilmoqda."
    await message.answer(text)
