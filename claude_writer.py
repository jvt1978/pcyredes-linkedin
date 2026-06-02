import anthropic
import os
import random
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def _call_claude(model, max_tokens, system, messages, retries=3, delay=30):
    for attempt in range(retries):
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages
            )
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < retries - 1:
                print(f"⚠️ Anthropic sobrecargado (529). Reintento {attempt+1}/{retries-1} en {delay}s...")
                time.sleep(delay)
            else:
                raise

SYSTEM_PROMPT = """Eres el community manager de PCyRedes, empresa de soporte IT y redes en Barcelona (www.pcyredes.com).
Escribes posts para LinkedIn dirigidos a responsables de empresa y directores IT de pymes en España.
Tono: educativo, claro y útil. Enseña algo concreto que el lector pueda aplicar o que le haga reflexionar.
Nunca uses lenguaje de vendedor. Aporta valor real en cada post."""

_BLOG_TOPICS = [
    "ciberseguridad para pymes",
    "copias de seguridad en la nube",
    "migración a Microsoft 365",
    "soporte IT externalizado vs interno",
    "ransomware: cómo prevenirlo",
    "redes wifi empresariales seguras",
    "productividad con herramientas digitales",
    "mantenimiento preventivo de infraestructura IT",
    "trabajo remoto seguro",
    "virtualización de servidores en pymes",
    "phishing: cómo detectarlo",
    "copilot de Microsoft en el día a día",
    "migración de Windows 10 a Windows 11",
    "NAS para empresas: cuándo tiene sentido",
    "antivirus empresarial: qué mirar",
]

def generate_linkedin_post(title: str, excerpt: str) -> str:
    message = _call_claude(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Escribe un post educativo para LinkedIn basado en este artículo del blog de PCyRedes.\n\n"
                f"Título del artículo: {title}\n"
                + (f"Extracto: {excerpt}\n\n" if excerpt else "\n")
                + "Infiere el tema del título y escribe el post.\n\n"
                "El post debe tener:\n"
                "- Una primera línea que enseñe o sorprenda (sin emoji al inicio)\n"
                "- 3-4 puntos con → que aporten algo concreto y aplicable\n"
                "- Una pregunta al final para generar conversación\n"
                "- 4 hashtags del sector IT B2B en España\n"
                "- Máximo 200 palabras\n"
                "- Incluye al final: 🔗 pcyredes.com"
            )
        }]
    )
    return message.content[0].text

def generate_standalone_post() -> str:
    topic = random.choice(_BLOG_TOPICS)
    message = _call_claude(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Escribe un post educativo para LinkedIn sobre: {topic}.\n"
                "Enfocado en pymes y empresas en España.\n\n"
                "El post debe tener:\n"
                "- Una primera línea que enseñe o sorprenda (sin emoji al inicio)\n"
                "- 3-4 puntos con → que aporten algo concreto y aplicable\n"
                "- Una pregunta al final para generar conversación\n"
                "- 4 hashtags del sector IT B2B en España\n"
                "- Máximo 200 palabras\n"
                "- Incluye al final: 🔗 pcyredes.com"
            )
        }]
    )
    return message.content[0].text
