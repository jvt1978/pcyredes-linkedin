import os
import logging
from dotenv import load_dotenv
from rss_checker import get_new_posts, mark_as_published
from claude_writer import generate_linkedin_post, generate_standalone_post
from linkedin_poster import post_to_linkedin
from image_creator import create_post_image
from notifier import notify_ceo

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    filename=os.path.join(_DIR, "marketing.log"),
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

def run():
    print("=== PCyRedes LinkedIn Bot ===\n")
    new_posts = get_new_posts()

    if not new_posts:
        print("No hay posts nuevos. Generando post educativo de temática IT...\n")
        linkedin_text = generate_standalone_post()
        print(linkedin_text)
        image_path = create_post_image(linkedin_text[:80])
        result = post_to_linkedin(linkedin_text, image_path)
        linkedin_id = result.get('id', 'OK')
        print(f"\n✓ Publicado: {linkedin_id}")
        logging.info(f"Standalone post publicado: {linkedin_id}")
        notify_ceo("Post educativo IT", "pcyredes.com", linkedin_id)
        return

    post = new_posts[0]
    print(f"Nuevo post: {post['title']}")
    print(f"URL: {post['link']}\n")

    linkedin_text = generate_linkedin_post(post["title"], post["excerpt"])
    print(linkedin_text)

    image_path = create_post_image(post["title"])
    result = post_to_linkedin(linkedin_text, image_path)
    mark_as_published(post["link"])
    linkedin_id = result.get('id', 'OK')
    print(f"\n✓ Publicado: {linkedin_id}")
    logging.info(f"Post publicado para {post['link']}: {linkedin_id}")
    notify_ceo(post["title"], post["link"], linkedin_id)

if __name__ == "__main__":
    run()
