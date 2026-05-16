import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLISHED_FILE = os.path.join(_DIR, "published.json")
SITEMAP_URL = "https://www.pcyredes.com/sitemap-blog-es.xml"

def load_published() -> set:
    if not os.path.exists(PUBLISHED_FILE):
        return set()
    with open(PUBLISHED_FILE, "r") as f:
        return set(json.load(f))

def save_published(published: set):
    with open(PUBLISHED_FILE, "w") as f:
        json.dump(list(published), f, indent=2)

def slug_to_title(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").capitalize()

def normalize_url(url: str) -> str:
    return url.replace("https://www.", "https://").rstrip("/")

def get_new_posts() -> list:
    published = {normalize_url(u) for u in load_published()}

    headers = {"User-Agent": "Mozilla/5.0 (compatible; PCyRedesBot/1.0)"}
    r = requests.get(SITEMAP_URL, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "xml")
    urls = soup.find_all("url")

    new_posts = []
    for url_tag in urls:
        loc = url_tag.find("loc")
        lastmod = url_tag.find("lastmod")
        if not loc:
            continue

        link = normalize_url(loc.get_text(strip=True))

        # Skip root /blog listing page
        if link.rstrip("/").endswith("/blog"):
            continue

        if link in published:
            continue

        pub_date = lastmod.get_text(strip=True) if lastmod else str(datetime.now().date())
        title = slug_to_title(link)

        new_posts.append({
            "title": title,
            "link": link,  # already normalized
            "excerpt": "",
            "published": pub_date
        })

    return new_posts

def mark_as_published(url: str):
    published = load_published()
    published.add(url)
    save_published(published)
