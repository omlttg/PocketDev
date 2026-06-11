import os
import httpx
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
group_id = os.getenv("TELEGRAM_GROUP_CHAT_ID")

print(f"Token: {token[:10]}...")
print(f"Group ID: {group_id}")

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {
    "chat_id": group_id,
    "text": "🔔 <b>Test Group Message</b>\nThis is a test notification from PocketDev.",
    "parse_mode": "HTML"
}

try:
    response = httpx.post(url, json=payload, timeout=10.0)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error sending message:", e)
