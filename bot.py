import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def welcome(message: types.Message):
    await message.answer("Добро пожаловать в SG Hotline!")

if __name__ == "__main__":
    executor.start_polling(dp)
