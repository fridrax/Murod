import asyncpg
from config import DATABASE_URL

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
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
        await conn.close()
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
