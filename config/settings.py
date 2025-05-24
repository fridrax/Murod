from aiogram import Bot, Dispatcher

# Задаём переменные вручную
BOT_TOKEN = "7548380199:AAFrTiLUGVcN1lIQ3t2pCZ8JZlgcwAnYe0c"
DATABASE_URL = "postgres://sg_hotline_user:EqdmK2EVuZGI0XTA6qTFJEW60NotR6dp@dbn-15l5pvs73k6diq-sg.hotline.db/sg_hotline_db"

# Создаём экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
