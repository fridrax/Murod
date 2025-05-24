from aiogram import executor
from loader import dp
from handlers.status import register_handlers

register_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
