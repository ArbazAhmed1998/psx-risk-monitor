import logging
import re

logger = logging.getLogger(__name__)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("vaderSentiment not installed, using fallback")

PSX_POSITIVE = {
    "dividend", "buyback", "right issue", "bonus share", "profit after tax",
    "earnings beat", "revenue growth", "margin expansion", "credit rating",
    "upgrade", "outperform", "market share", "expansion", "acquisition",
    "contract award", "project win", "capacity expansion", "exports surge",
    "remittance", "foreign investment", "rate cut", "subsidy", "allocation",
    "pipeline", "discovery", "reserve addition", "efficiency gain",
    "cost reduction", "debt repayment", "cash dividend", "stock split",
}

PSX_NEGATIVE = {
    "loss after tax", "earnings miss", "revenue decline", "margin contraction",
    "downgrade", "default", "default risk", "liquidity crisis", "circular debt",
    "write off", "impairment", "penalty", "investigation", "show cause",
    "suspension", "delisting", "insolvency", "bankruptcy", "layoff",
    "production halt", "plant shutdown", "power outage", "gas shortage",
    "currency devaluation", "rate hike", "inflation", "tax imposition",
    "levy", "regulatory risk", "political risk", "uncertainty",
    "protest", "strike", "blockade", "supply chain disruption",
}

NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "nothing", "nobody",
                  "hardly", "barely", "scarcely", "doesn't", "don't", "didn't",
                  "won't", "wouldn't", "couldn't", "shouldn't", "isn't", "aren't",
                  "wasn't", "weren't", "hasn't", "haven't", "hadn't"}

INTENSIFIERS = {"very", "highly", "extremely", "strongly", "significantly",
                "remarkably", "exceptionally", "notably", "substantially",
                "massively", "heavily", "deeply", "severely", "sharply"}


def analyze_sentiment(text: str) -> dict:
    if not text or not text.strip():
        return {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0, "label": "neutral"}

    if VADER_AVAILABLE:
        scores = _analyzer.polarity_scores(text)
    else:
        scores = _fallback_sentiment(text)

    psx_boost = _psx_sentiment_boost(text)
    compound = scores["compound"] + psx_boost
    compound = max(-1.0, min(1.0, compound))

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {**scores, "compound": compound, "label": label}


def _psx_sentiment_boost(text: str) -> float:
    text_lower = text.lower()
    boost = 0.0
    for word in PSX_POSITIVE:
        if word in text_lower:
            boost += 0.08
    for word in PSX_NEGATIVE:
        if word in text_lower:
            boost -= 0.12
    return max(-0.5, min(0.5, boost))


def _fallback_sentiment(text: str) -> dict:
    positive_words = {"up", "gain", "rise", "profit", "growth", "positive", "strong", "surge",
                      "record", "bullish", "recovery", "boost", "rally", "outperform", "success",
                      "improve", "increase", "high", "best", "win", "benefit", "good", "great"}
    negative_words = {"down", "loss", "fall", "decline", "drop", "negative", "weak", "crash",
                      "bearish", "selloff", "plunge", "debt", "crisis", "risk", "pressure",
                      "fail", "cut", "low", "worst", "lose", "damage", "bad", "poor", "worry"}

    text_lower = text.lower()
    words = text_lower.split()
    pos_count = 0
    neg_count = 0
    i = 0
    while i < len(words):
        word = words[i].strip(".,!?;:\"'()[]")
        is_negated = any(
            words[i - 1].strip(".,!?;:\"'()[]") in NEGATION_WORDS
            for j in range(max(0, i - 2), i)
        ) if i > 0 else False

        multiplier = 1.0
        if is_negated:
            multiplier = -1.0
        for j in range(max(0, i - 3), i):
            if words[j].strip(".,!?;:\"'()[]") in INTENSIFIERS:
                multiplier *= 1.5 if not is_negated else 1.3
                break

        if word in positive_words:
            pos_count += 1 * multiplier if multiplier > 0 else 0
            neg_count += abs(multiplier) if multiplier < 0 else 0
        elif word in negative_words:
            neg_count += 1 * multiplier if multiplier > 0 else 0
            pos_count += abs(multiplier) if multiplier < 0 else 0

        i += 1

    for phrase in PSX_POSITIVE:
        if phrase in text_lower:
            pos_count += 2
    for phrase in PSX_NEGATIVE:
        if phrase in text_lower:
            neg_count += 3

    total = pos_count + neg_count
    if total == 0:
        return {"compound": 0.0, "positive": 0.0, "negative": 0.0, "neutral": 1.0}

    compound = (pos_count - neg_count) / (total + 5) * 2
    compound = max(-1.0, min(1.0, compound))
    return {
        "compound": compound,
        "positive": pos_count / total if pos_count > 0 else 0.0,
        "negative": neg_count / total if neg_count > 0 else 0.0,
        "neutral": 0.0 if total > 0 else 1.0,
    }
