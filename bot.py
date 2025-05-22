from aiogram import executor
from loader import dp
from database import init_db
import handlers  # подтянет всё из handlers/__init__.py

async def on_startup(dispatcher):
    await init_db()

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
