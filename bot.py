import os
import asyncpg
import asyncio
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime

BOT_TOKEN = "7548380199:AAHuimOasDC-QQrJBn2xrpKTtbwnR_L7rY0"
DATABASE_URL = os.getenv("DATABASE_URL")

TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

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

WELCOME_TEXTS = {
    "ru": (
        "👋 <b>SG Hotline</b> — это анонимная платформа обращений компании «STAR GROUP».\n"
        "Здесь вы можете анонимно отправить своё сообщение руководству. Гарантируется, что каждое сообщение будет доставлено и получит должное внимание!\n\n"
        "Если вы хотите сообщить о нарушениях или неправомерных действиях, пожалуйста, предоставьте как можно более подробную информацию. "
        "Укажите, что именно произошло, где и когда это случилось. Такие детали крайне важны для того, чтобы мы могли оперативно и эффективно предпринять необходимые меры. "
        "Ваша помощь поможет нам поддерживать высокие стандарты работы и обеспечивать соблюдение корпоративных норм."
    ),
    "uz": (
        "👋 <b>SG Hotline</b> — bu «STAR GROUP» kompaniyasining anonim murojaat platformasidir.\n"
        "Bu yerda siz rahbariyatga o‘z xabaringizni anonim tarzda yuborishingiz mumkin. Har bir xabar albatta yetkaziladi va lozim darajada e’tiborga olinadi!\n\n"
        "Agar siz qoidabuzarliklar yoki noqonuniy harakatlar haqida xabar bermoqchi bo‘lsangiz, iltimos, imkon qadar batafsil ma’lumot bering. "
        "Nima bo‘lganini, qayerda va qachon sodir bo‘lganini ko‘rsating. Bunday tafsilotlar bizga tezkor va samarali choralar ko‘rish imkoniyatini beradi. "
        "Sizning yordamchingiz bizga yuqori ish standartlarini saqlash va korporativ me’yorlarga rioya qilishga yordam beradi."
    )
}

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = None
    await callback.message.edit_reply_markup()
    # Показываем приветствие сразу после выбора языка
    await callback.message.answer(WELCOME_TEXTS[lang], parse_mode="HTML")
    await callback.message.answer(
        "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:",
        reply_markup=main_menu_keyboard(lang)
    )

CITIES_RU = [
    "Ташкент", "Самаркандская область", "Бухарская область", "Наманганская область",
    "Андижанская область", "Ферганская область", "Навоийская область", "Кашкадарьинская область",
    "Республика Каракалпакстан", "Хорезмская область", "Джизакская область",
    "Сырдарьинская область", "Сурхандарьинская область", "Ташкентская область"
]

CITIES_UZ = [
    "Toshkent", "Samarqand viloyati", "Buxoro viloyati", "Namangan viloyati",
    "Andijon viloyati", "Farg‘ona viloyati", "Navoiy viloyati", "Qashqadaryo viloyati",
    "Qoraqalpog‘iston Respublikasi", "Xorazm viloyati", "Jizzax viloyati",
    "Sirdaryo viloyati", "Surxondaryo viloyati", "Toshkent viloyati"
]

@dp.message_handler(lambda m: m.text in ["📝 Оставить заявку", "📝 Murojaat qoldirish"])
async def new_ticket(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = "city"
    prompt = "📍 Выберите или введите ваш город:" if lang == "ru" else "📍 Shaharingizni tanlang yoki kiriting:"
    back_text = "◀️ Назад" if lang == "ru" else "◀️ Orqaga"
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Добавляем города
    cities = CITIES_RU if lang == "ru" else CITIES_UZ
    for city in cities:
        kb.add(KeyboardButton(city))
    kb.add(KeyboardButton(back_text))
    await message.answer(prompt, reply_markup=kb)

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
    await message.answer("🏢 Укажите свой отдел или напишите:" if lang == "ru" else "🏢 Bo'limingizni ko'rsating yoki yozing:", reply_markup=kb)

def city_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cities = CITIES_RU if lang == "ru" else CITIES_UZ
    for city in cities:
        kb.insert(KeyboardButton(city))
    kb.add(KeyboardButton("◀️ Назад" if lang == "ru" else "◀️ Orqaga"))
    return kb

@dp.message_handler(lambda m: user_state.get(m.from_user.id) == "department")
async def get_problem(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    lang = user_data[user_id]["lang"]
    back_text = "◀️ Назад" if lang == "ru" else "◀️ Orqaga"
    if text == back_text:
        user_state[user_id] = "city"
        # Показываем клавиатуру с городами!
        kb = city_keyboard(lang)  # Вот здесь используем функцию с городами
        await message.answer(
            "📍 Напишите из какого вы города:" if lang == "ru" else "📍 Qaysi shahardan ekanligingizni yozing:",
            reply_markup=kb
        )
        return
    user_data[user_id]["department"] = text
    user_state[user_id] = "problem"
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(back_text))
    await message.answer(
        "📝 Подробно опишите свою проблему:" if lang == "ru" else "📝 Muammoni batafsil tavsiflang:",
        reply_markup=kb
    )

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
        await message.answer("🏢 Укажите свой отдел или напишите:" if lang == "ru" else "🏢 Bo'limingizni ko'rsating yoki yozing:", reply_markup=kb)
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
        f"✅ Ваше обращение зарегистрировано под номером №{ticket_number} и будет рассмотрено руководством."
        if lang == "ru" else
        f"✅ Murojaatingiz №{ticket_number} raqam bilan ro'yxatga olindi va rahbariyat tomonidan ko‘rib chiqiladi."
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
💬 <b>Ответ:</b> Пока без ответа
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    keyboard.add(
    InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh|{ticket_number}")
    )
    await bot.send_message(admin_chat_id, text, reply_markup=keyboard)

@dp.message_handler(lambda m: m.text in ["📋 Статус заявки", "📊 Murojaat holati"])
async def show_status(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "ru")
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM tickets WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10", user_id)
    await conn.close()

    def format_dt(dt):
        if dt is None:
            return ''
        # Если из БД приходит naive datetime, делаем aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(TASHKENT_TZ).strftime('%Y-%m-%d %H:%M')

    if not rows:
        await message.answer(
            "❗️ У вас пока нет заявок." if lang == "ru" else "❗️ Sizda hali hech qanday murojaat yo'q."
        )
        return

    if lang == "ru":
        text = "🗂 <b>Последние заявки:</b>\n\n"
        for row in rows:
            text += (
                f"<b>№{row['ticket_number']}</b> — {format_dt(row['created_at'])}\n"
                f"📌 Статус: <i>{row['status']}</i>"
                + (f" (обновлено: {format_dt(row['status_updated_at'])})" if row['status_updated_at'] else "") + "\n"
                f"📝 {row['message'][:100]}\n"
                f"💬 Ответ: {row['reply'] or 'Пока без ответа'}\n\n"
            )
    else:
        text = "🗂 <b>So‘nggi murojaatlar:</b>\n\n"
        for row in rows:
            text += (
                f"<b>№{row['ticket_number']}</b> — {format_dt(row['created_at'])}\n"
                f"📌 Holat: <i>{row['status']}</i>"
                + (f" (yangilandi: {format_dt(row['status_updated_at'])})" if row['status_updated_at'] else "") + "\n"
                f"📝 {row['message'][:100]}\n"
                f"💬 Javob: {row['reply'] or 'Hozircha javob yo‘q'}\n\n"
            )

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard(lang))

@dp.callback_query_handler(lambda c: c.data.startswith("status|"))
async def update_status(callback: types.CallbackQuery):
    _, ticket_number, new_status = callback.data.split("|")
    now = datetime.now(TASHKENT_TZ)  # текущее время с таймзоной Узбекистана

    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "UPDATE tickets SET status=$1, status_updated_at=$2 WHERE ticket_number=$3",
        new_status, now, ticket_number
    )
    row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_number=$1", ticket_number)
    await conn.close()

    def format_dt(dt):
        if dt is None:
            return ''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.astimezone(TASHKENT_TZ).strftime('%Y-%m-%d %H:%M')

    user_id = row['user_id']
    lang = row['lang']
    status_notify = {
        "В работе": f"⏳ Ваша заявка №{ticket_number} принята в работу.\nДата: {format_dt(now)}",
        "Завершено": f"✅ Ваша заявка №{ticket_number} успешно завершена.\nДата: {format_dt(now)}",
        "Отклонено": f"❌ Ваша заявка №{ticket_number} отклонена.\nДата: {format_dt(now)}",
    }
    status_notify_uz = {
        "В работе": f"⏳ Murojaatingiz №{ticket_number} ko'rib chiqilmoqda.\nSana: {format_dt(now)}",
        "Завершено": f"✅ Murojaatingiz №{ticket_number} muvaffaqiyatli yakunlandi.\nSana: {format_dt(now)}",
        "Отклонено": f"❌ Murojaatingiz №{ticket_number} rad etildi.\nSana: {format_dt(now)}",
    }
    notify = status_notify.get(new_status) if lang == "ru" else status_notify_uz.get(new_status)
    if notify:
        await bot.send_message(user_id, notify)

    status_text = {
        "Новая": "🟢 Новая",
        "В работе": "🟡 В работе",
        "Завершено": "✅ Завершено",
        "Отклонено": "🔴 Отклонено"
    }.get(new_status, new_status)

    text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата создания:</b> {format_dt(row['created_at'])}
🎫 <b>Номер:</b> №{row['ticket_number']}
🌐 <b>Язык:</b> {"Русский" if row['lang'] == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {row['city']}
🏢 <b>Отдел:</b> {row['department']}
📝 <b>Сообщение:</b> {row['message']}
📌 <b>Статус:</b> <i>{status_text}</i>
🕓 <b>Дата статуса:</b> {format_dt(row['status_updated_at']) if row['status_updated_at'] else ''}
💬 <b>Ответ:</b> {row['reply'] or "Пока без ответа"}
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
    )
    keyboard.add(
        InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh|{ticket_number}")
    )
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer("Статус изменен!")

# Обработка нажатия на "Настройки"
@dp.message_handler(lambda m: m.text in ["⚙️ Настройки", "⚙️ Sozlamalar"])
async def settings_menu(message: types.Message):
    lang = user_data.get(message.from_user.id, {}).get("lang", "ru")
    kb = InlineKeyboardMarkup()
    if lang == "ru":
        kb.add(InlineKeyboardButton("🌐 Изменить язык", callback_data="change_lang"))
    else:
        kb.add(InlineKeyboardButton("🌐 Tilni o‘zgartirish", callback_data="change_lang"))
    await message.answer(
        "Настройки:" if lang == "ru" else "Sozlamalar:",
        reply_markup=kb
    )

# Показываем выбор языка
@dp.callback_query_handler(lambda c: c.data == "change_lang")
async def show_lang_select(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz")
    )
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer("Выберите язык" if user_data.get(callback.from_user.id, {}).get("lang", "ru") == "ru" else "Tilni tanlang")

# Смена языка из настроек (этот handler уже есть, не дублируй — просто убедись, что он не ограничен только стартом!)
@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data[user_id] = {"lang": lang}
    user_state[user_id] = None
    await callback.message.edit_reply_markup()  # удаляем кнопки выбора языка
    await callback.message.answer(
        "Язык изменён! Выберите действие:" if lang == "ru" else "Til o‘zgartirildi! Amalni tanlang:",
        reply_markup=main_menu_keyboard(lang)
    )

@dp.message_handler(lambda m: m.chat.id == -4680581564 and m.text.startswith("/reply"))
async def reply_user(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.reply("⚠️ Формат: /reply 00001 текст")
        return

    ticket_number, reply_text = parts[1], parts[2]
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_number = $1", ticket_number)
    if not row:
        await message.reply("❌ Тикет не найден.")
        await conn.close()
        return
    user_id = row["user_id"]
    try:
        await bot.send_message(user_id, f"📩 Ответ по тикету №{ticket_number}:\n\n{reply_text}")
        await conn.execute("UPDATE tickets SET reply = $1 WHERE ticket_number = $2", reply_text, ticket_number)
        row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_number = $1", ticket_number)

        status_text = {
            "Новая": "🟢 Новая",
            "В работе": "🟡 В работе",
            "Завершено": "✅ Завершено",
            "Отклонено": "🔴 Отклонено"
        }.get(row['status'], row['status'])

        text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {row['created_at'].strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{row['ticket_number']}
🌐 <b>Язык:</b> {"Русский" if row['lang'] == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {row['city']}
🏢 <b>Отдел:</b> {row['department']}
📝 <b>Сообщение:</b> {row['message']}
📌 <b>Статус:</b> <i>{status_text}</i>
💬 <b>Ответ:</b> {row['reply'] or "Пока без ответа"}
""".strip()

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
            InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
            InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
            InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено")
        )
        keyboard.add(
            InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh|{ticket_number}")
        )
        if message.reply_to_message:
            await message.reply_to_message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

        await message.reply("✅ Ответ успешно отправлен пользователю.")
    except Exception as e:
        await message.reply(f"❌ Ошибка отправки ответа: {e}")
    await conn.close()
# Для запуска и инициализации базы
@dp.callback_query_handler(lambda c: c.data.startswith("refresh|"))
async def refresh_ticket(callback: types.CallbackQuery):
    ticket_number = callback.data.split("|")[1]
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_number = $1", ticket_number)
    await conn.close()
    if not row:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return

    status_text = {
        "Новая": "🟢 Новая",
        "В работе": "🟡 В работе",
        "Завершено": "✅ Завершено",
        "Отклонено": "🔴 Отклонено"
    }.get(row['status'], row['status'])

    text = f"""
📨 <b>Новая заявка</b>
🗓 <b>Дата:</b> {row['created_at'].strftime('%Y-%m-%d %H:%M')}
🎫 <b>Номер:</b> №{row['ticket_number']}
🌐 <b>Язык:</b> {"Русский" if row['lang'] == "ru" else "O‘zbekcha"}
📍 <b>Город:</b> {row['city']}
🏢 <b>Отдел:</b> {row['department']}
📝 <b>Сообщение:</b> {row['message']}
📌 <b>Статус:</b> <i>{status_text}</i>
💬 <b>Ответ:</b> {row['reply'] or "Пока без ответа"}
""".strip()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✉️ Ответить", switch_inline_query_current_chat=f"/reply {ticket_number}"),
        InlineKeyboardButton("🟡 В работу", callback_data=f"status|{ticket_number}|В работе"),
        InlineKeyboardButton("🟢 Завершено", callback_data=f"status|{ticket_number}|Завершено"),
        InlineKeyboardButton("🔴 Отклонено", callback_data=f"status|{ticket_number}|Отклонено"),
    )
    keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh|{ticket_number}"))

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("Заявка обновлена!")
    except MessageNotModified:
        await callback.answer("Нет изменений для обновления.", show_alert=False)
    
async def main():
    await init_db()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
