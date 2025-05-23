from aiogram import types
from handlers.start import user_data
import sqlite3

async def show_status(message: types.Message):
    """Retrieve the list of user’s tickets from the database and send to the user."""
    user_id = message.from_user.id
    # Determine user's language (default to Russian if not set)
    lang = user_data.get(user_id, {}).get("lang", "ru")

    # Query the database for this user's tickets
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT id, status FROM tickets WHERE user_id=?", (user_id,))
    records = cur.fetchall()
    conn.close()

    if not records:
        # No tickets found for this user
        if lang == "ru":
            await message.answer("❗ Вы еще не оставляли заявок.")
        else:
            await message.answer("❗ Siz hali birorta murojaat qoldirmagansiz.")
    else:
        # Build the response listing each ticket with its status
        if lang == "ru":
            header = "📋 *Список ваших заявок:*\n"
        else:
            header = "📋 *Murojaatlaringiz ro‘yxati:*\n"
        lines = []
        for ticket_id, status in records:
            ticket_no = f"№{ticket_id:05d}"
            if status:
                # If status is stored in Russian, it can be shown directly; otherwise, consider translation if needed
                lines.append(f"{ticket_no} — {status}")
            else:
                lines.append(f"{ticket_no}")
        # Send the compiled list (formatting in Markdown for bold header, if supported)
        await message.answer(header + "\n".join(lines), parse_mode="Markdown")
