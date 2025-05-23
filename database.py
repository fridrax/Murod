import asyncpg
from config import DATABASE_URL

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                lang TEXT NOT NULL,
                city TEXT,
                department TEXT,
                message TEXT,
                ticket_number TEXT UNIQUE,
                status TEXT DEFAULT 'Новая',
                reply TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        await conn.close()
        print("✅ Таблица tickets проверена или создана.")
    except Exception as e:
        print(f"❌ Ошибка при подключении к базе данных: {e}")
