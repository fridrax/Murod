from aiogram import types
from aiogram.types import CallbackQuery
from loader import dp
from keyboards import lang_keyboard, main_menu

# Global dictionaries to track user data and state
user_state = {}
user_data = {}

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    # Ignore the /start command if used in a group chat
    if message.chat.type != "private":
        return  # Игнорируем команду в групповых чатах

    # Prompt the user to choose a language
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=lang_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    """Handles language selection from inline buttons."""
    lang = callback.data.split("_")[1]       # Extract the selected language code (e.g., "ru" or "uz")
    user_id = callback.from_user.id

    # Initialize user data for this user
    user_data[user_id] = {
        "lang": lang,
        "city": None,
        "department": None,
        "message": None
    }
    user_state[user_id] = None  # No active state yet (will be set when user starts a ticket)

    # Remove the language keyboard and acknowledge the callback
    await callback.message.edit_reply_markup()  # Remove inline buttons after selection
    await callback.answer()

    # Show the main menu (actions) in the selected language
    await callback.message.answer(
        "🔻 Выберите действие:" if lang == "ru" else "🔻 Amalni tanlang:",
        reply_markup=main_menu(lang)
    )

@dp.message_handler(lambda m: m.text in ["📊 Статус заявки", "📊 Murojaat holati"])
async def handle_status_request(message: types.Message):
    """Handles the "Status of requests" action from the main menu."""
    user_id = message.from_user.id
    # Ensure the user has an entry in user_data (in case bot restarted and lost data)
    if user_id not in user_data:
        user_data[user_id] = {"lang": "ru", "city": None, "department": None, "message": None}

    # Import and call the show_status function to retrieve and send the list of tickets
    from handlers.status import show_status
    await show_status(message)
