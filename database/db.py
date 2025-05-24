import asyncpg
import logging
from config.settings import DATABASE_URL

async def init_db():
    logging.info("Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        logging.info("Database connected, creating table...")
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                lang TEXT,
                city TEXT,
                department TEXT,
                message TEXT,
                ticket_number TEXT,
                status TEXT,
                reply TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        logging.info("Table created.")
    except Exception as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        await conn.close()
