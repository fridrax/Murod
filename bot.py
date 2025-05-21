import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Токен прописан напрямую
BOT_TOKEN = "7548380199:AAF2yqncpxlTZeBekP3heA8b_N23oNGEmNw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def welcome(message: types.Message):
    await message.answer("Добро пожаловать в SG Hotline!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
