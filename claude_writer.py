"""Redactor de posts de LinkedIn para PCyRedes.

Flujo:
  1. generate_ideas()  -> 3 ideas nuevas, nunca repetidas (historial en topics_history.json)
  2. ceo_pick()        -> Alejandro (CEO) elige una
  3. write_post()      -> borrador + revisión editorial, alternando tono formal / cercano
  4. register_post()   -> guarda tema y tono para no repetir y alternar
"""
from __future__ import annotations

import anthropic
import json
import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv

_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, ".env"), override=True)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

WRITER_MODEL = os.getenv("WRITER_MODEL", "claude-opus-5-5")
FALLBACK_MODEL = "claude-sonnet-4-6"

# En Railway el disco se borra en cada deploy: monta un Volume y pon DATA_DIR=/data
DATA_DIR = os.getenv("DATA_DIR", _DIR)
HISTORY_FILE = os.path.join(DATA_DIR, "topics_history.json")


# ---------------------------------------------------------------- Claude ----

def _call_claude(max_tokens, system, messages, retries=3, delay=30, model=None):
    model = model or WRITER_MODEL
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model=model, max_tokens=max_tokens, system=system, messages=messages
            )
            return msg.content[0].text.strip()
        except anthropic.NotFoundError:
            if model != FALLBACK_MODEL:
                print(f"⚠️ Modelo {model} no disponible. Uso {FALLBACK_MODEL}.")
                model = FALLBACK_MODEL
                continue
            raise
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < retries - 1:
                print(f"⚠️ Anthropic sobrecargado (529). Reintento {attempt+1}/{retries-1} en {delay}s...")
                time.sleep(delay)
            else:
                raise


def _extract_json(text):
    match = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    return json.loads(match.group(1) if match else text)


# -------------------------------------------------------------- Historial ----

def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def register_post(topic: str, tone: str, linkedin_id: str = ""):
    history = load_history()
    history.append({
        "date": str(datetime.now().date()),
        "topic": topic,
        "tone": tone,
        "linkedin_id": linkedin_id,
    })
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def next_tone() -> str:
    """Alterna: si el último fue formal, hoy toca cercano, y al revés."""
    history = load_history()
    if not history:
        return "formal"
    return "cercano" if history[-1].get("tone") == "formal" else "formal"


# ------------------------------------------------------------- Estilo -------

BRAND = """PCyRedes es una empresa de soporte IT, redes, ciberseguridad y Microsoft 365 en Barcelona,
con 19 años atendiendo a pymes (www.pcyredes.com). Los posts se publican en la página de empresa
y los leen gerentes, directores financieros y responsables de oficina de pymes en España.
No son técnicos: quieren entender el riesgo, el coste y qué hacer el lunes."""

TONES = {
    "formal": (
        "TONO DE HOY: FORMAL. Trato de usted o impersonal. Frases completas y precisas, "
        "vocabulario de dirección de empresa (riesgo, coste, continuidad, responsabilidad). "
        "Sin coloquialismos ni emojis en el cuerpo. Serio, nunca rígido."
    ),
    "cercano": (
        "TONO DE HOY: CERCANO. Trato de tú. Habla como un técnico con años de oficio "
        "contándole algo a un cliente con un café: frases cortas, alguna expresión cotidiana, "
        "algo de humor si sale natural. Como mucho un emoji en todo el post. Cercano, nunca infantil."
    ),
}

STYLE_RULES = """ESTRUCTURA OBLIGATORIA:
1. GANCHO (líneas 1-2). Es lo único que se ve antes de "ver más". Debe ser una de estas formas:
   - un dato concreto y sorprendente,
   - una escena real ("El lunes a las 9 nos llamó una gestoría de Sabadell: nadie podía abrir el correo."),
   - una afirmación incómoda que el lector reconozca en su empresa.
   Nunca empieces con una pregunta retórica genérica, con "En el mundo actual", "Hoy en día" ni con la palabra del tema.
2. EJEMPLO REAL. Un caso concreto de pyme (tipo de negocio, ciudad o comarca, nº de empleados, qué pasó,
   cuánto costó o cuánto tiempo estuvo parada). Los casos son ilustrativos y anónimos: nunca nombres de clientes reales.
   Las cifras de estudios solo si son de dominio público y conocidas; si dudas, usa el caso en vez del dato.
3. QUÉ HACER. 2-4 acciones concretas que el lector pueda aplicar esta semana, cada una en una línea que empiece por →.
   Concretas significa con verbo y objeto: "Prueba a restaurar un archivo de la copia del viernes", no "Revisa tus copias".
4. PREGUNTA FINAL. Una sola pregunta, específica y fácil de contestar en un comentario
   ("¿Cuándo fue la última vez que restaurasteis algo de la copia?"), nunca "¿Qué opinas?".
5. Línea en blanco, 3-4 hashtags del sector IT B2B en España, y al final: 🔗 pcyredes.com

REGLAS DE ESCRITURA:
- Entre 120 y 200 palabras. Párrafos de 1-2 frases, con línea en blanco entre ellos.
- Voz activa y sujeto humano: "el gerente perdió tres días", no "se produjo una pérdida".
- Específico antes que general: nombres de herramientas, cifras, plazos, lugares.
- Prohibido: frases de arranque de relleno, "no es X, es Y" y cualquier contraste binario parecido,
  rayas largas (—), listas de lo que algo NO es, frases sueltas de una palabra para dar dramatismo,
  adverbios en -mente salvo que sean imprescindibles, jerga de negocio
  (sinergia, potenciar, ecosistema, transformación digital, solución integral, en el mundo actual, clave, crucial, robusto),
  lenguaje de vendedor y llamadas a contratar. Sin negritas ni markdown (LinkedIn no lo muestra).
- Afirma con seguridad. Nada de "podría", "quizás", "es posible que" sin necesidad.
- Ritmo variado: mezcla frases cortas y medias."""

EXAMPLE = """EJEMPLO DE NIVEL ESPERADO (tono cercano, solo como referencia de calidad; no copies el tema ni las frases):

Una academia de Terrassa con 12 empleados pagó 3.000 € por recuperar sus archivos. Tenía copia de seguridad.

El problema: la copia estaba en un disco conectado al mismo servidor. El ransomware cifró las dos cosas a la vez.

Lo vemos cada mes. La copia existe, pero nadie ha comprobado que sirve el día que hace falta.

Tres cosas que puedes hacer esta semana:

→ Desconecta una copia del servidor o llévala a la nube con versiones
→ Elige un archivo al azar y restáuralo. Cronometra cuánto tardas
→ Apunta quién avisa a quién si un lunes nada funciona

Una copia que nunca has restaurado es una apuesta.

¿Cuándo fue la última vez que recuperasteis algo de vuestra copia?

#Ciberseguridad #CopiasDeSeguridad #SoporteIT #Pymes

🔗 pcyredes.com"""


# --------------------------------------------------------------- Ideas -------

def generate_ideas(n: int = 3, blog_articles: list | None = None) -> list:
    """Devuelve n ideas nuevas: [{"topic", "angle", "source"}]. Nunca repite temas del historial."""
    used = [h["topic"] for h in load_history()]
    # Artículos del blog ya llevados a LinkedIn antes de este cambio
    published_file = os.path.join(_DIR, "published.json")
    if os.path.exists(published_file):
        with open(published_file, encoding="utf-8") as f:
            used += [u.rstrip("/").split("/")[-1].replace("-", " ") for u in json.load(f)]
    blog_block = ""
    if blog_articles:
        lines = "\n".join(f"- {a['title']} ({a['link']})" for a in blog_articles[:5])
        blog_block = (
            "\nArtículos nuevos del blog de PCyRedes que pueden ser una de las ideas "
            f"(si usas uno, pon su URL en \"source\"):\n{lines}\n"
        )
    prompt = (
        f"Propón {n} ideas de post de LinkedIn para PCyRedes, distintas entre sí "
        "(no todas de ciberseguridad: alterna redes, Microsoft 365, copias, puestos de trabajo, "
        "IA en la oficina, normativa, costes IT, continuidad de negocio, etc.).\n\n"
        "TEMAS YA PUBLICADOS (prohibido repetirlos o publicar el mismo enfoque con otras palabras):\n"
        + ("\n".join(f"- {t}" for t in used[-120:]) or "- (ninguno todavía)")
        + "\n" + blog_block
        + "\nCada idea necesita un ángulo concreto con un caso o dato que sirva de gancho, "
        "no un tema genérico. Ejemplo de ángulo bueno: \"La impresora de red como puerta de entrada: "
        "el caso de un despacho que tenía el firmware de 2019\".\n\n"
        "Responde SOLO con JSON: "
        '[{"topic": "tema en 3-6 palabras", "angle": "ángulo concreto en una frase", "source": ""}]'
    )
    text = _call_claude(800, BRAND, [{"role": "user", "content": prompt}])
    return _extract_json(text)[:n]


def ceo_pick(ideas: list) -> dict:
    """Alejandro, CEO de PCyRedes, elige la idea con más potencial."""
    options = "\n".join(f"{i+1}. {x['topic']}: {x['angle']}" for i, x in enumerate(ideas))
    system = (
        "Eres Alejandro, CEO de PCyRedes. Eliges qué publica la empresa en LinkedIn. "
        "Priorizas lo que un gerente de pyme reconocería en su propia oficina, lo que genera "
        "conversación y lo que refuerza la confianza en PCyRedes. " + BRAND
    )
    prompt = (
        f"Estas son las 3 ideas para hoy:\n{options}\n\n"
        'Elige una. Responde SOLO con JSON: {"choice": número, "reason": "una frase"}'
    )
    data = _extract_json(_call_claude(200, system, [{"role": "user", "content": prompt}]))
    idx = max(0, min(len(ideas) - 1, int(data.get("choice", 1)) - 1))
    chosen = dict(ideas[idx])
    chosen["ceo_reason"] = data.get("reason", "")
    return chosen


# --------------------------------------------------------------- Redacción ---

def write_post(topic: str, angle: str = "", tone: str | None = None, source_url: str = "") -> tuple[str, str]:
    """Escribe el post en dos pasadas (borrador + revisión). Devuelve (texto, tono)."""
    tone = tone or next_tone()
    system = f"{BRAND}\n\nEres el redactor de LinkedIn de PCyRedes.\n\n{TONES[tone]}\n\n{STYLE_RULES}\n\n{EXAMPLE}"

    brief = f"Tema: {topic}\n"
    if angle:
        brief += f"Ángulo: {angle}\n"
    if source_url:
        brief += f"Se basa en este artículo del blog: {source_url} (menciónalo de forma natural antes de los hashtags).\n"

    draft = _call_claude(900, system, [{
        "role": "user",
        "content": brief + "\nEscribe el post. Devuelve solo el texto del post, sin comentarios.",
    }])

    review = (
        "Actúa como editor exigente. Revisa este borrador contra las reglas y la estructura.\n"
        "Comprueba en concreto:\n"
        "- ¿Las dos primeras líneas harían parar el scroll a un gerente? Si no, reescríbelas.\n"
        "- ¿Hay un ejemplo real y concreto con negocio, lugar y consecuencia?\n"
        "- ¿Cada → es una acción aplicable esta semana?\n"
        "- ¿La pregunta final es específica y fácil de contestar?\n"
        f"- ¿Se mantiene el tono {tone.upper()} de principio a fin?\n"
        "- ¿Aparece alguna palabra o construcción prohibida? Elimínala.\n"
        "- ¿Está entre 120 y 200 palabras?\n\n"
        "Devuelve SOLO la versión final corregida del post, sin explicaciones.\n\n"
        f"BORRADOR:\n{draft}"
    )
    final = _call_claude(900, system, [{"role": "user", "content": review}])
    final = final.replace("—", ",").replace("**", "")
    return final, tone


# ------------------------------------------------- Compatibilidad antigua ---

def generate_linkedin_post(title: str, excerpt: str = "") -> str:
    return write_post(title, excerpt)[0]


def generate_standalone_post() -> str:
    idea = ceo_pick(generate_ideas())
    return write_post(idea["topic"], idea["angle"])[0]
