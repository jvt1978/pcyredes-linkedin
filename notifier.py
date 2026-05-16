import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
CEO_NUMBER = os.getenv("CEO_WHATSAPP_NUMBER")

def notify_ceo(post_title: str, post_url: str, linkedin_id: str):
    message = (
        f"✅ *PCyRedes LinkedIn Bot*\n\n"
        f"Post publicado correctamente:\n"
        f"📝 *{post_title}*\n"
        f"🔗 {post_url}\n\n"
        f"ID LinkedIn: `{linkedin_id}`"
    )

    response = requests.post(
        f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "messaging_product": "whatsapp",
            "to": CEO_NUMBER,
            "type": "text",
            "text": {"body": message}
        }
    )

    if response.ok:
        print(f"📱 Alejandro notificado por WhatsApp")
    else:
        print(f"⚠️  WhatsApp no enviado: {response.status_code} {response.text}")
