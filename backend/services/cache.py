import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RISK_CACHE_FILE = os.path.join(CACHE_DIR, "risk_cache.json")
NEWS_CACHE_FILE = os.path.join(CACHE_DIR, "news_cache.json")
TRAINING_DATA_FILE = os.path.join(CACHE_DIR, "training_data.json")

os.makedirs(CACHE_DIR, exist_ok=True)


def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load cache {path}: {e}")
        return {}


def _save_json(path: str, data: dict):
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Failed to save cache {path}: {e}")


def get_cached_risk(symbol: str) -> dict | None:
    cache = _load_json(RISK_CACHE_FILE)
    entry = cache.get(symbol)
    if not entry:
        return None
    cached_date = entry.get("date", "")
    if cached_date != datetime.now().strftime("%Y-%m-%d"):
        return None
    return entry.get("result")


def set_cached_risk(symbol: str, result: dict):
    cache = _load_json(RISK_CACHE_FILE)
    cache[symbol] = {"date": datetime.now().strftime("%Y-%m-%d"), "result": result}
    _save_json(RISK_CACHE_FILE, cache)


def get_cached_news(symbol: str) -> list | None:
    cache = _load_json(NEWS_CACHE_FILE)
    entry = cache.get(symbol)
    if not entry:
        return None
    cached_time = entry.get("timestamp", 0)
    if datetime.now().timestamp() - cached_time > 21600:
        return None
    return entry.get("articles")


def set_cached_news(symbol: str, articles: list):
    cache = _load_json(NEWS_CACHE_FILE)
    cache[symbol] = {"timestamp": datetime.now().timestamp(), "articles": articles}
    _save_json(NEWS_CACHE_FILE, cache)


def append_training_data(symbol: str, features: list, target: int):
    cache = _load_json(TRAINING_DATA_FILE)
    if symbol not in cache:
        cache[symbol] = []
    cache[symbol].append({"features": features, "target": target})
    cache[symbol] = cache[symbol][-500:]
    _save_json(TRAINING_DATA_FILE, cache)


def get_all_training_data() -> tuple[list, list]:
    cache = _load_json(TRAINING_DATA_FILE)
    all_features = []
    all_targets = []
    for symbol, entries in cache.items():
        for entry in entries:
            all_features.append(entry["features"])
            all_targets.append(entry["target"])
    return all_features, all_targets
