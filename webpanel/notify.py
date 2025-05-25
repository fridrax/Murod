# notify.py
import requests

BOT_TOKEN = "7548380199:AAHDNiBN_YFr2wH4SKm_eVfD-zbFQVw8TQo"  # вставь свой токен бота
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
