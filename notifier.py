import requests

def send(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    r = requests.post(url, json=payload, timeout=15)
    if r.status_code != 200:
        print("❌ Telegram error:", r.status_code, r.text)
    else:
        print("✅ Telegram sent")
