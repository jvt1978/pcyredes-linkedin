import os
import logging
import requests
import anthropic
from dotenv import load_dotenv
from rss_checker import get_new_posts, mark_as_published
from claude_writer import generate_ideas, ceo_pick, write_post, register_post
from linkedin_poster import post_to_linkedin
from image_creator import create_post_image
from notifier import notify_ceo, notify_error

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    filename=os.path.join(_DIR, "marketing.log"),
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

def run():
    print("=== PCyRedes LinkedIn Bot ===\n")
    try:
        blog_articles = get_new_posts()
    except Exception as e:
        logging.warning(f"No se pudo leer el sitemap del blog: {e}")
        blog_articles = []

    # 1. Tres ideas nuevas (los artículos nuevos del blog entran como candidatos)
    ideas = generate_ideas(3, blog_articles)
    for i, idea in enumerate(ideas, 1):
        print(f"Idea {i}: {idea['topic']} | {idea['angle']}")

    # 2. El CEO elige
    chosen = ceo_pick(ideas)
    print(f"\nAlejandro elige: {chosen['topic']} ({chosen.get('ceo_reason', '')})\n")

    # 3. Redacción con tono alterno
    linkedin_text, tone = write_post(chosen["topic"], chosen["angle"], source_url=chosen.get("source", ""))
    print(f"[tono: {tone}]\n{linkedin_text}")

    # 4. Publicar y registrar
    image_path = create_post_image(chosen["topic"])
    result = post_to_linkedin(linkedin_text, image_path)
    linkedin_id = result.get('id', 'OK')
    register_post(chosen["topic"], tone, linkedin_id)
    if chosen.get("source"):
        mark_as_published(chosen["source"])
    print(f"\n✓ Publicado: {linkedin_id}")
    logging.info(f"Post publicado [{tone}] '{chosen['topic']}': {linkedin_id}")
    notify_ceo(f"{chosen['topic']} (tono {tone})", chosen.get("source") or "pcyredes.com", linkedin_id)

if __name__ == "__main__":
    try:
        run()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            logging.error("LinkedIn token caducado (401)")
            notify_error("linkedin_token")
        else:
            logging.error(f"HTTP error: {e}")
            notify_error("generic", str(e))
    except anthropic.BadRequestError as e:
        if "credit balance" in str(e):
            logging.error("Anthropic sin créditos (400)")
            notify_error("anthropic_credits")
        else:
            logging.error(f"Anthropic error: {e}")
            notify_error("generic", str(e))
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        notify_error("generic", str(e))
