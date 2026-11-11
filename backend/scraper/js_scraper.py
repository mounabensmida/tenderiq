"""Scraper pour les pages dynamiques, avec un vrai navigateur sans fenêtre (headless).

Lancer :
    python -m backend.scraper.js_scraper https://quotes.toscrape.com/js/ "div.quote"
"""
import json
import sys
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

from backend.app.core.config import ROOT


def scrape(url: str, item_selector: str) -> list[dict]:
    rows = []
    with sync_playwright() as p:                      # démarre Playwright
        browser = p.chromium.launch(headless=True)    # headless = sans fenêtre visible
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")      # attend que la page ait fini de charger
        page.wait_for_selector(item_selector)         # attend que le JavaScript ait affiché les avis
        for element in page.locator(item_selector).all():
            rows.append({
                "source": "playwright",
                "url": url,
                "raw_text": element.inner_text(),     # le texte visible du bloc
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })
        browser.close()
    return rows


if __name__ == "__main__":
    url, selector = sys.argv[1], sys.argv[2]           # les 2 arguments de la ligne de commande
    rows = scrape(url, selector)
    out = ROOT / "data" / "raw" / "tenders_js.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} éléments écrits dans {out}")