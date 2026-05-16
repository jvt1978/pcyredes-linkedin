import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"

# PCyRedes brand colors
COLOR_BG       = (12, 35, 75)      # Azul marino oscuro
COLOR_ACCENT   = (0, 120, 215)     # Azul corporativo
COLOR_WHITE    = (255, 255, 255)
COLOR_GRAY     = (180, 200, 220)
COLOR_STRIPE   = (0, 90, 170)      # Franja lateral

W, H = 1200, 628  # LinkedIn optimal size


def _wrap_text(text, font, draw, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_post_image(title: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = os.path.join(_DIR, "post_image.jpg")

    img = Image.new("RGB", (W, H), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Franja lateral izquierda
    draw.rectangle([0, 0, 8, H], fill=COLOR_ACCENT)

    # Franja superior decorativa
    draw.rectangle([0, 0, W, 6], fill=COLOR_ACCENT)

    # Bloque inferior
    draw.rectangle([0, H - 90, W, H], fill=COLOR_STRIPE)
    draw.rectangle([0, H - 92, W, H - 90], fill=COLOR_ACCENT)

    # Logo / nombre empresa
    try:
        font_logo = ImageFont.truetype(FONT_BOLD, 38)
    except Exception:
        font_logo = ImageFont.load_default()
    draw.text((50, 45), "pcyredes", fill=COLOR_ACCENT, font=font_logo)
    draw.text((50, 88), "Soporte IT · Redes · Barcelona", fill=COLOR_GRAY,
              font=ImageFont.truetype(FONT_REGULAR, 22) if os.path.exists(FONT_REGULAR) else font_logo)

    # Línea separadora
    draw.rectangle([50, 130, W - 50, 133], fill=COLOR_ACCENT)

    # Título principal (texto del post — primeras 12 palabras)
    short_title = " ".join(title.split()[:14])
    if len(title.split()) > 14:
        short_title += "..."

    try:
        font_title = ImageFont.truetype(FONT_BOLD, 52)
    except Exception:
        font_title = ImageFont.load_default()

    lines = _wrap_text(short_title.upper(), font_title, draw, W - 140)
    y = 165
    for line in lines[:4]:
        draw.text((50, y), line, fill=COLOR_WHITE, font=font_title)
        y += 68

    # Icono LinkedIn
    try:
        font_icon = ImageFont.truetype(FONT_BOLD, 22)
    except Exception:
        font_icon = ImageFont.load_default()
    draw.text((50, H - 63), "www.pcyredes.com", fill=COLOR_WHITE, font=font_icon)

    # Hashtag decorativo
    draw.text((W - 320, H - 63), "#SoporteIT  #PymesEspaña", fill=COLOR_GRAY, font=font_icon)

    img.save(output_path, "JPEG", quality=92)
    return output_path
