import asyncio
from loader import dp
from database import init_db
import handlers  # подтянет все из handlers/__init__.py
from aiogram import executor

async def on_startup(dispatcher):
    await init_db()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())  # инициализируем БД до запуска
    executor.start_polling(dp, skip_updates=True)
