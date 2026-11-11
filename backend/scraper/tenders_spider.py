"""Spider Scrapy générique pour une page qui liste des appels d'offres.

Lancer :
    scrapy runspider backend/scraper/tenders_spider.py -O data/raw/tenders.jsonl
Les sélecteurs marqués "À ADAPTER" dépendent du site visé (clic droit > Inspecter).
"""
from datetime import datetime, timezone

import scrapy


class TendersSpider(scrapy.Spider):
    name = "tenders"
    start_urls = ["https://quotes.toscrape.com"]          # À REMPLACER par la page de liste du site visé

    # Réglages de politesse : respecter robots.txt, attendre 2 s entre 2 pages, se présenter.
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 2,
        "USER_AGENT": "TenderIQ-student-bot (projet pedagogique)",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def parse(self, response):
        """Appelée sur chaque page de LISTE. On suit chaque lien vers le détail."""
        for card in response.css("div.quote"):                  # À ADAPTER : un bloc = un avis
            link = card.css("a[href^='/author/']::attr(href)").get()   # lien qui commence par /author/
            if link:
                # response.follow transforme un lien relatif en URL complète et planifie la visite.
                yield response.follow(link, callback=self.parse_detail)

        next_page = response.css("li.next a::attr(href)").get() # À ADAPTER : bouton "page suivante"
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_detail(self, response):
        """Appelée sur chaque page de DÉTAIL. On garde le texte brut : le LLM structurera plus tard."""
        texts = response.css("div.author-details ::text").getall()   # seulement la zone utile
        raw_text = "\n".join(t.strip() for t in texts if t.strip())
        pdfs = [response.urljoin(h) for h in response.css("a[href$='.pdf']::attr(href)").getall()]
        # "yield" renvoie un élément à Scrapy, qui l'écrit dans le fichier de sortie (-O).
        yield {
            "source": self.name,
            "url": response.url,
            "raw_text": raw_text,
            "pdf_urls": pdfs,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }