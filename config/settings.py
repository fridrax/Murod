import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Загружаем переменные окружения из .env (для локального запуска)
load_dotenv()

# Получаем токен и DATABASE_URL из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Проверяем, что переменные заданы
if not BOT_TOKEN or not DATABASE_URL:
    raise ValueError("BOT_TOKEN and DATABASE_URL must be set in environment variables")

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
