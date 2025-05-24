import os
import sys
import asyncio
import logging

# Настраиваем пути для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import bot, dp
from database.db import init_db
from handlers.commands import register_commands
from handlers.tickets import register_tickets
from handlers.admin import register_admin

logging.basicConfig(level=logging.INFO)

async def main():
    logging.info("Initializing database...")
    await init_db()
    logging.info("Registering handlers...")
    register_commands(dp)
    register_tickets(dp)
    register_admin(dp)
    logging.info("Starting bot...")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
