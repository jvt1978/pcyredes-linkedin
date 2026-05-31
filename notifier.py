import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
CEO_NUMBER = os.getenv("CEO_WHATSAPP_NUMBER")

def _send_whatsapp(message: str):
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
        print(f"📱 WhatsApp enviado")
    else:
        print(f"⚠️  WhatsApp no enviado: {response.status_code} {response.text}")

def notify_error(error_type: str, details: str = ""):
    messages = {
        "linkedin_token": (
            "⚠️ *PCyRedes LinkedIn Bot — ERROR*\n\n"
            "El token de LinkedIn ha caducado (401 Unauthorized).\n\n"
            "🔧 Acción necesaria:\n"
            "Renueva el token OAuth en LinkedIn Developer Portal y actualiza LINKEDIN_ACCESS_TOKEN en Railway."
        ),
        "anthropic_credits": (
            "⚠️ *PCyRedes LinkedIn Bot — ERROR*\n\n"
            "Saldo de Anthropic agotado (400 Bad Request).\n\n"
            "🔧 Acción necesaria:\n"
            "Recarga créditos en console.anthropic.com/billing"
        ),
        "generic": (
            f"⚠️ *PCyRedes LinkedIn Bot — ERROR*\n\n"
            f"Error inesperado:\n`{details[:300]}`"
        ),
    }
    message = messages.get(error_type, messages["generic"])
    _send_whatsapp(message)

def notify_ceo(post_title: str, post_url: str, linkedin_id: str):
    message = (
        f"✅ *PCyRedes LinkedIn Bot*\n\n"
        f"Post publicado correctamente:\n"
        f"📝 *{post_title}*\n"
        f"🔗 {post_url}\n\n"
        f"ID LinkedIn: `{linkedin_id}`"
    )

    _send_whatsapp(message)
