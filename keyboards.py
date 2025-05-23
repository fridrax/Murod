from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Выбор языка
def lang_keyboard():
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz")
    )

# Главное меню
def main_menu(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "ru":
        kb.add(KeyboardButton("📝 Оставить заявку"), KeyboardButton("📊 Статус заявки"))
        kb.add(KeyboardButton("⚙️ Настройки"))
    else:
        kb.add(KeyboardButton("📝 Murojaat qoldirish"), KeyboardButton("📊 Murojaat holati"))
        kb.add(KeyboardButton("⚙️ Sozlamalar"))
    return kb

# Выбор отдела
def departments_keyboard(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    items = ["Продажи", "Технический", "Сервис"] if lang == "ru" else ["Sotuv", "Texnik", "Xizmat"]
    back_text = "◀️ Назад" if lang == "ru" else "◀️ Orqaga"

    for i in items:
        kb.add(KeyboardButton(i))
    kb.add(KeyboardButton(back_text))
    return kb
