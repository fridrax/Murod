# notify.py
import requests

BOT_TOKEN = "7548380199:AAHMfpJovucWaSk25a6b2UFo7j0pa72WLl4"  # вставь свой токен бота
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def notify_user(user_id, message):
    data = {
        "chat_id": user_id,
        "text": message
    }
    try:
        requests.post(TG_API, data=data)
    except Exception as e:
        print("Notify error:", e)
