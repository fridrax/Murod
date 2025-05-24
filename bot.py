from aiogram import executor
from loader import dp
import handlers  # Импорт всех хендлеров через __init__.py

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
