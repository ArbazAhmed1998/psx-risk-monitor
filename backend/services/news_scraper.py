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
    {
        "name": "Profits.pk",
        "url": "https://profit.pakistantoday.com.pk/?s={symbol}",
        "parser": "profits",
    },
]


def scrape_news(symbol: str, max_articles: int = 10) -> list[dict]:
    all_articles = []
    for source in SOURCES:
        try:
            url = source["url"].format(symbol=symbol)
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            parser = source["parser"]
            items = _parsers[parser](soup, source["name"])
            all_articles.extend(items)
        except Exception as e:
            logger.warning(f"Failed to scrape {source['name']} for {symbol}: {e}")
            continue

    all_articles = _deduplicate(all_articles)
    all_articles = all_articles[:max_articles]

    for article in all_articles:
        try:
            from backend.services.sentiment import analyze_sentiment
        except ImportError:
            from services.sentiment import analyze_sentiment
        score = analyze_sentiment(article["title"] + " " + article["snippet"])
        article["sentiment"] = score["label"]
        article["sentiment_score"] = score["compound"]

    return all_articles


def _deduplicate(articles: list[dict]) -> list[dict]:
    seen_titles = set()
    unique = []
    for a in articles:
        key = re.sub(r"[^a-z0-9]", "", a["title"].lower())[:80]
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique.append(a)
    return unique


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


def _parse_profits(soup: BeautifulSoup, source: str) -> list[dict]:
    items = []
    for article in soup.select("article, .post, .search-result")[:5]:
        title_el = article.select_one("h2 a, h3 a, .entry-title a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        if link and not link.startswith("http"):
            link = "https://profit.pakistantoday.com.pk" + link
        snippet_el = article.select_one(".excerpt, .entry-summary, p")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        date_el = article.select_one("time, .date, .published")
        date = date_el.get("datetime", "") if date_el else datetime.now().isoformat()
        items.append({"title": title, "source": source, "url": link, "date": date, "snippet": snippet})
    return items


_parsers = {
    "brecorder": _parse_brecorder,
    "tribune": _parse_tribune,
    "dawn": _parse_dawn,
    "profits": _parse_profits,
}
