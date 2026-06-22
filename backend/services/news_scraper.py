import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SOURCES = [
    {
        "name": "Business Recorder",
        "url": "https://www.brecorder.com/search/{symbol}",
        "parser": "brecorder",
    },
    {
        "name": "The Express Tribune",
        "url": "https://tribune.com.pk/search/{symbol}",
        "parser": "tribune",
    },
    {
        "name": "Dawn",
        "url": "https://www.dawn.com/search?q={symbol}",
        "parser": "dawn",
    },
]


def scrape_news(symbol: str, max_articles: int = 10) -> list[dict]:
    articles = []
    for source in SOURCES:
        try:
            url = source["url"].format(symbol=symbol)
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            parser = source["parser"]
            if parser == "brecorder":
                items = _parse_brecorder(soup, source["name"])
            elif parser == "tribune":
                items = _parse_tribune(soup, source["name"])
            elif parser == "dawn":
                items = _parse_dawn(soup, source["name"])
            else:
                items = []
            articles.extend(items)
        except Exception as e:
            logger.warning(f"Failed to scrape {source['name']} for {symbol}: {e}")
            continue

    articles = articles[:max_articles]
    for article in articles:
        from services.sentiment import analyze_sentiment
        score = analyze_sentiment(article["title"] + " " + article["snippet"])
        article["sentiment"] = score["label"]
        article["sentiment_score"] = score["compound"]

    return articles


def _parse_brecorder(soup: BeautifulSoup, source: str) -> list[dict]:
    items = []
    for article in soup.select("article, .story, .news-item")[:5]:
        title_el = article.select_one("h2 a, h3 a, .title a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link and not link.startswith("http"):
            link = "https://www.brecorder.com" + link
        snippet_el = article.select_one(".summary, p, .description")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        date_el = article.select_one("time, .date, .published")
        date = date_el.get("datetime", "") if date_el else datetime.now().isoformat()
        items.append({"title": title, "source": source, "url": link, "date": date, "snippet": snippet})
    return items


def _parse_tribune(soup: BeautifulSoup, source: str) -> list[dict]:
    items = []
    for article in soup.select("article, .story-card, .post-card")[:5]:
        title_el = article.select_one("h2 a, h3 a, .title a, .headline a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link and not link.startswith("http"):
            link = "https://tribune.com.pk" + link
        snippet_el = article.select_one(".summary, .excerpt, p")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        date_el = article.select_one("time, .date, .published")
        date = date_el.get("datetime", "") if date_el else datetime.now().isoformat()
        items.append({"title": title, "source": source, "url": link, "date": date, "snippet": snippet})
    return items


def _parse_dawn(soup: BeautifulSoup, source: str) -> list[dict]:
    items = []
    for article in soup.select("article, .story, .search-result")[:5]:
        title_el = article.select_one("h2 a, h3 a, .title a, .story__headline a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link and not link.startswith("http"):
            link = "https://www.dawn.com" + link
        snippet_el = article.select_one(".story__excerpt, .summary, p")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        date_el = article.select_one("time, .date, .timestamp")
        date = date_el.get("datetime", "") if date_el else datetime.now().isoformat()
        items.append({"title": title, "source": source, "url": link, "date": date, "snippet": snippet})
    return items
