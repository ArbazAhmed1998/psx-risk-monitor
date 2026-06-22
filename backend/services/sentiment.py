import logging

logger = logging.getLogger(__name__)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("vaderSentiment not installed, using fallback")


def analyze_sentiment(text: str) -> dict:
    if not text or not text.strip():
        return {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0, "label": "neutral"}
    if VADER_AVAILABLE:
        scores = _analyzer.polarity_scores(text)
    else:
        scores = _fallback_sentiment(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {**scores, "label": label}


def _fallback_sentiment(text: str) -> dict:
    positive_words = {"up", "gain", "rise", "profit", "growth", "positive", "strong", "surge",
                      "record", "bullish", "recovery", "boost", "rally", "outperform"}
    negative_words = {"down", "loss", "fall", "decline", "drop", "negative", "weak", "crash",
                      "bearish", "selloff", "plunge", "debt", "crisis", "risk", "pressure"}
    text_lower = text.lower()
    words = set(text_lower.split())
    pos_count = len(words & positive_words)
    neg_count = len(words & negative_words)
    total = pos_count + neg_count
    if total == 0:
        return {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0}
    compound = (pos_count - neg_count) / total
    return {
        "compound": compound,
        "positive": pos_count / total if pos_count > 0 else 0.0,
        "negative": neg_count / total if neg_count > 0 else 0.0,
        "neutral": 0.0 if total > 0 else 1.0,
    }
