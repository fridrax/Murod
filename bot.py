import os
import asyncpg
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime

BOT_TOKEN = "7548380199:AAHM_1x2BObercvZGtuw4mD1qEDWlGcct5o"
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

user_state = {}
user_data = {}

async def init_db():
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

def main_menu_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add(KeyboardButton("📝 Оставить заявку"), KeyboardButton("📋 Статус заявки"))
        kb.add(KeyboardButton("⚙️ Настройки"))
    else:
        kb.add(KeyboardButton("📝 Murojaat qoldirish"), KeyboardButton("📊 Murojaat holati"))
        kb.add(KeyboardButton("⚙️ Sozlamalar"))
    return kb

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz")
    )
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=keyboard)
    user_state.pop(message.from_user.id, None)
    user_data.pop(message.from_user.id, None)

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = None
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:",
        reply_markup=main_menu_keyboard(lang)
    )

@dp.message_handler(lambda m: m.text in ["📝 Оставить заявку", "📝 Murojaat qoldirish"])
async def new_ticket(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = "city"
    prompt = "📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:"
    # Меню убираем, чтобы пользователь не видел главное меню при заполнении заявки
    await message.answer(prompt, reply_markup=ReplyKeyboardRemove())

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "city")
async def get_department(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    lang = user_data[user_id]["lang"]
    # Проверка на кнопку "Назад"
    if text in ["◀️ Назад", "◀️ Orqaga"]:
        await message.answer("Главное меню.", reply_markup=main_menu_keyboard(lang))
        user_state[user_id] = None
        return
    user_data[user_id]["city"] = text
    user_state[user_id] = "department"
    # Клавиатура с отделами + кнопка назад
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    items = ["Продажи", "Технический", "Сервис"] if lang == "ru" else ["Sotuv", "Texnik", "Xizmat"]
    back_text = "◀️ Назад" if lang == "ru" else "◀️ Orqaga"
    for i in items:
        kb.add(KeyboardButton(i))
    kb.add(KeyboardButton(back_text))
    await message.answer("🏢 Выберите отдел:" if lang == "ru" else "🏢 Bo‘limni tanlang:", reply_markup=kb)

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
async def get_problem(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    lang = user_data[user_id]["lang"]
    # Кнопка назад
    if text in ["◀️ Назад", "◀️ Orqaga"]:
        user_state[user_id] = "city"
        await message.answer("📍 Укажите ваш город:" if lang == "ru" else "📍 Shahringizni kiriting:", reply_markup=ReplyKeyboardRemove())
        return
    user_data[user_id]["department"] = text
    user_state[user_id] = "problem"
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    back_text = "◀️ Назад" if lang == "ru" else "◀️ Orqaga"
    kb.add(KeyboardButton(back_text))
    await message.answer("📝 Опишите проблему:" if lang == "ru" else "📝 Muammoni batafsil yozing:", reply_markup=kb)

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "problem")
async def save_ticket(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    lang = user_data[user_id]["lang"]
    # Кнопка назад
    if text in ["◀️ Назад", "◀️ Orqaga"]:
        user_state[user_id] = "department"
        # Отделы
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        items = ["Продажи", "Технический", "Сервис"] if lang == "ru" else ["Sotuv", "Texnik", "Xizmat"]
        back_text = "◀️ Назад" if lang == "ru" else "◀️ Orqaga"
        for i in items:
            kb.add(KeyboardButton(i))
        kb.add(KeyboardButton(back_text))
        await message.answer("🏢 Выберите отдел:" if lang == "ru" else "🏢 Bo‘limni tanlang:", reply_markup=kb)
        return

    user_data[user_id]["message"] = text
    conn = await asyncpg.connect(DATABASE_URL)
    count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
    ticket_number = str(count + 1).zfill(5)
    await conn.execute('''
        INSERT INTO tickets (user_id, lang, city, department, message, ticket_number, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    ''', user_id, lang, user_data[user_id]["city"], user_data[user_id]["department"], user_data[user_id]["message"], ticket_number, "Новая")
    await conn.close()

    confirm = (
        f"✅ Ваше обращение зарегистрировано под номером №{ticket_number}"
        if lang == "ru" else
        f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi."
    )
    await message.answer(confirm, reply_markup=main_menu_keyboard(lang))
    user_state.pop(user_id, None)

    # Уведомление в группу
    admin_chat_id = -4680581564
    text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{ticket_number}
🌐 <b>Язык:</b> {"Русский" if lang == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {user_data[user_id]['city']}
🏢 <b>Отдел:</b> {user_data[user_id]['department']}
📝 <b>Сообщение:</b> {user_data[user_id]['message']}
📌 <b>Статус:</b> <i>Новая</i>
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    await bot.send_message(admin_chat_id, text, reply_markup=keyboard)

@dp.message_handler(lambda m: m.text in ["📋 Статус заявки", "📊 Murojaat holati"])
async def show_status(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM tickets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10", user_id)
    await conn.close()

    if not rows:
        await message.answer("❗️ У вас пока нет заявок." if lang == "ru" else "❗️ Sizda hali hech qanday murojaat yo'q.")
        return

    text = "🗂 <b>Последние заявки:</b>\n\n" if lang == "ru" else "🗂 <b>So‘nggi murojaatlar:</b>\n\n"
    for row in rows:
        text += (
            f"<b>№{row['ticket_number']}</b> — {row['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"📌 Статус: <i>{row['status']}</i>\n"
            f"📝 {row['message'][:100]}\n\n"
        )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard(lang))

@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def update_status(callback: types.CallbackQuery):
    _, ticket_number, new_status = callback.data.split("|")
    # Обновляем статус в базе
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("UPDATE tickets SET status=$1 WHERE ticket_number=$2", new_status, ticket_number)
    row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_number=$1", ticket_number)
    await conn.close()

    # --- Уведомление пользователя о смене статуса ---
    user_id = row['user_id']
    lang = row['lang']
    status_notify = {
        "В работе": "⏳ Ваша заявка принята в работу.",
        "Завершено": "✅ Ваша заявка успешно завершена.",
        "Отклонено": "❌ Ваша заявка отклонена.",
    }
    status_notify_uz = {
        "В работе": "⏳ Murojaatingiz ko'rib chiqilmoqda.",
        "Завершено": "✅ Murojaatingiz muvaffaqiyatli yakunlandi.",
        "Отклонено": "❌ Murojaatingiz rad etildi.",
    }
    notify = status_notify.get(new_status) if lang == "ru" else status_notify_uz.get(new_status)
    if notify:
        await bot.send_message(user_id, notify)

    # --- Формируем новое сообщение в группе с обновлённым статусом ---
    status_text = {
        "Новая": "🟢 Новая",
        "В работе": "🟡 В работе",
        "Завершено": "✅ Завершено",
        "Отклонено": "🔴 Отклонено"
    }.get(new_status, new_status)

    text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {row['created_at'].strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{row['ticket_number']}
🌐 <b>Язык:</b> {"Русский" if row['lang'] == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {row['city']}
🏢 <b>Отдел:</b> {row['department']}
📝 <b>Сообщение:</b> {row['message']}
📌 <b>Статус:</b> <i>{status_text}</i>
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    # Обновляем сообщение в группе
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("Статус изменен!")

@dp.message_handler(lambda m: m.chat.id == -4680581564 and m.text.startswith("/reply"))
async def reply_user(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("⚠️ Формат: /reply 00001 текст")
        return
    ticket_number, reply_text = parts[1], parts[2]
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT user_id FROM tickets WHERE ticket_number = $1", ticket_number)
    if not row:
        await message.reply("❌ Тикет не найден.")
        await conn.close()
        return
    user_id = row["user_id"]
    await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")
    await conn.execute("UPDATE tickets SET reply = $1 WHERE ticket_number = $2", reply_text, ticket_number)
    await conn.close()
    await message.reply("✅ Ответ отправлен.")
# Для запуска и инициализации базы
async def main():
    await init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
