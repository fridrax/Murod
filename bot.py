from aiogram import executor
from loader import dp
from database import init_db
import handlers  # Импорт всех хендлеров через __init__.py

# Функция запуска при старте бота
async def on_startup(dispatcher):
    await init_db()  # Инициализация подключения к БД

if __name__ == "__main__":
    # Стартуем бота и передаём функцию on_startup
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
