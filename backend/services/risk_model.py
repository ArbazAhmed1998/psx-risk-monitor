import pandas as pd
import numpy as np
from datetime import datetime
import logging
import joblib
import os

from backend.services import psx_data
from backend.services.indicators import latest_indicators, add_all_indicators
from backend.services.news_scraper import scrape_news
from backend.services.sentiment import analyze_sentiment
from backend.services.cache import (
    get_cached_risk, set_cached_risk,
    get_cached_news, set_cached_news,
    append_training_data, get_all_training_data,
)

logger = logging.getLogger(__name__)

ML_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "risk_classifier.pkl")


def calculate_risk(symbol: str) -> dict | None:
    cached = get_cached_risk(symbol)
    if cached:
        return cached

    df = psx_data.get_historical(symbol, days=365)
    if df is None or len(df) < 50:
        logger.warning(f"Not enough data for {symbol} to compute risk")
        return None

    ind = latest_indicators(df)
    quote = psx_data.get_quote(symbol)

    news_articles = get_cached_news(symbol)
    if news_articles is None:
        news_articles = scrape_news(symbol)
        set_cached_news(symbol, news_articles)

    avg_sentiment = _average_news_sentiment(news_articles)

    tech_score = _technical_score(ind, df)
    momentum_score = _momentum_score(ind)
    trend_score = _trend_score(ind)
    volume_score = _volume_score(ind)
    news_score = _news_score(avg_sentiment)
    vol_score = _volatility_score(df)

    base_score = tech_score
    total_score = base_score + momentum_score + trend_score + volume_score + news_score + vol_score
    total_score = max(0, min(100, total_score))

    if total_score <= 30:
        risk_level = "LOW"
    elif total_score <= 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    ml_pred = _ml_predict(symbol, df, avg_sentiment, ind)

    explanation = _build_explanation(
        ind, avg_sentiment, volume_score,
        news_score, vol_score, total_score,
        momentum_score, trend_score,
    )

    result = {
        "symbol": symbol,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "risk_score": round(total_score, 2),
        "risk_level": risk_level,
        "components": {
            "technical": round(base_score, 2),
            "momentum": round(momentum_score, 2),
            "trend": round(trend_score, 2),
            "volume": round(volume_score, 2),
            "news_sentiment": round(news_score, 2),
            "volatility": round(vol_score, 2),
        },
        "indicators": {
            "rsi": ind.get("rsi"),
            "macd": ind.get("macd"),
            "sma_20": ind.get("sma_20"),
            "sma_50": ind.get("sma_50"),
            "bb_position": ind.get("bb_position"),
            "atr_percent": ind.get("atr_percent"),
            "volume_change": ind.get("volume_change"),
            "stoch_rsi_k": ind.get("stoch_rsi_k"),
            "stoch_rsi_d": ind.get("stoch_rsi_d"),
            "roc": ind.get("roc"),
            "adx": ind.get("adx"),
            "sma_crossover": ind.get("sma_crossover"),
        },
        "ml_prediction": ml_pred,
        "explanation": explanation,
    }

    set_cached_risk(symbol, result)
    return result


def _technical_score(ind: dict, df: pd.DataFrame) -> float:
    score = 0.0

    rsi = ind.get("rsi")
    if rsi is not None:
        if rsi > 70:
            score += 10
        elif rsi > 60:
            score += 5
        elif rsi < 30:
            score -= 5
        elif rsi < 40:
            score -= 2
        elif 40 <= rsi <= 60:
            score -= 10

    macd = ind.get("macd")
    if macd == "bearish":
        score += 12
    elif macd == "bullish":
        score -= 8

    sma_20 = ind.get("sma_20")
    sma_50 = ind.get("sma_50")
    if sma_20 and sma_50 and len(df) >= 50:
        last_close = float(df.iloc[-1]["close"])
        if last_close < sma_20 and last_close < sma_50:
            score += 10
        elif last_close > sma_20 and last_close > sma_50:
            score -= 6
        elif last_close < sma_20:
            score += 4
        elif last_close > sma_20:
            score -= 2

    bb = ind.get("bb_position")
    if bb == "above":
        score += 8
    elif bb == "below":
        score -= 4

    return max(-5, min(35, score + 15))


def _momentum_score(ind: dict) -> float:
    score = 0.0

    stoch_k = ind.get("stoch_rsi_k")
    if stoch_k is not None:
        if stoch_k > 80:
            score += 6
        elif stoch_k > 60:
            score += 3
        elif stoch_k < 20:
            score -= 4
        elif stoch_k < 40:
            score -= 2

    roc = ind.get("roc")
    if roc is not None:
        if roc > 5:
            score -= 3
        elif roc > 2:
            score -= 1
        elif roc < -5:
            score += 4
        elif roc < -2:
            score += 2

    return max(-5, min(10, score))


def _trend_score(ind: dict) -> float:
    score = 0.0

    crossover = ind.get("sma_crossover")
    if crossover == "death_cross":
        score += 5
    elif crossover == "golden_cross":
        score -= 5

    adx = ind.get("adx")
    if adx is not None:
        if adx > 40:
            score += 4
        elif adx > 25:
            score += 1
        else:
            score -= 2

    return max(-5, min(10, score))


def _volume_score(ind: dict) -> float:
    score = 0.0

    vol_change = ind.get("volume_change")
    if vol_change is not None:
        if vol_change > 2.0:
            score += 5
        elif vol_change > 1.5:
            score += 3
        elif vol_change < 0.5:
            score -= 2
        elif vol_change < 0.3:
            score -= 4

    return max(-4, min(6, score + 2))


def _news_score(avg_sentiment: float) -> float:
    if avg_sentiment > 0.3:
        return 3.0
    elif avg_sentiment > 0.1:
        return 8.0
    elif avg_sentiment > -0.1:
        return 15.0
    elif avg_sentiment > -0.3:
        return 22.0
    else:
        return 28.0


def _volatility_score(df: pd.DataFrame) -> float:
    if len(df) < 20:
        return 10.0
    closes = df["close"].astype(float).tail(20)
    returns = closes.pct_change().dropna()
    daily_vol = returns.std()
    annual_vol = daily_vol * np.sqrt(252)
    if annual_vol > 0.5:
        return 18.0
    elif annual_vol > 0.4:
        return 15.0
    elif annual_vol > 0.3:
        return 12.0
    elif annual_vol > 0.2:
        return 8.0
    elif annual_vol > 0.15:
        return 5.0
    else:
        return 3.0


def _average_news_sentiment(articles: list) -> float:
    if not articles:
        return 0.0
    scores = []
    for a in articles:
        text = a.get("title", "") + " " + a.get("snippet", "")
        result = analyze_sentiment(text)
        scores.append(result["compound"])
    return float(np.mean(scores)) if scores else 0.0


def _build_explanation(ind: dict, avg_sentiment: float,
                        volume_score: float, news_score: float,
                        vol_score: float, total: float,
                        momentum_score: float, trend_score: float) -> list[str]:
    expl = []

    rsi = ind.get("rsi")
    if rsi is not None:
        if rsi > 70:
            expl.append(f"RSI at {rsi} — overbought territory")
        elif rsi < 30:
            expl.append(f"RSI at {rsi} — oversold territory")
        elif 40 <= rsi <= 60:
            expl.append(f"RSI at {rsi} — neutral zone")
        else:
            expl.append(f"RSI at {rsi} — leaning {'overbought' if rsi > 60 else 'oversold'}")

    stoch = ind.get("stoch_rsi_k")
    if stoch is not None:
        if stoch > 80:
            expl.append(f"Stochastic RSI at {stoch:.0f} — momentum overbought")
        elif stoch < 20:
            expl.append(f"Stochastic RSI at {stoch:.0f} — momentum oversold")

    macd = ind.get("macd")
    if macd:
        expl.append(f"MACD signal — {macd.upper()}")

    crossover = ind.get("sma_crossover")
    if crossover == "golden_cross":
        expl.append("SMA 50/200 — GOLDEN CROSS (bullish long-term)")
    elif crossover == "death_cross":
        expl.append("SMA 50/200 — DEATH CROSS (bearish long-term)")

    adx = ind.get("adx")
    if adx is not None:
        if adx > 40:
            expl.append(f"ADX at {adx:.0f} — strong trend")
        elif adx > 25:
            expl.append(f"ADX at {adx:.0f} — moderate trend")
        else:
            expl.append(f"ADX at {adx:.0f} — weak trend")

    roc = ind.get("roc")
    if roc is not None:
        if abs(roc) > 5:
            expl.append(f"Price momentum ({roc:+.1f}% ROC) — strong {'downward' if roc < 0 else 'upward'}")

    bb = ind.get("bb_position")
    if bb and bb != "middle":
        expl.append(f"Price is {bb.upper()} Bollinger Bands")

    vol_change = ind.get("volume_change")
    if vol_change is not None and vol_change > 1.5:
        expl.append(f"Volume spike — {vol_change:.1f}x above average")

    if avg_sentiment < -0.1:
        expl.append("Negative news sentiment detected")
    elif avg_sentiment > 0.1:
        expl.append("Positive news sentiment detected")
    else:
        expl.append("Neutral news sentiment")

    expl.append(f"Technical: {total - news_score - vol_score - volume_score:.0f}/50")
    expl.append(f"Momentum: {momentum_score:.0f}/10 | Trend: {trend_score:.0f}/10")
    expl.append(f"News: {news_score:.0f}/30 | Volatility: {vol_score:.0f}/20")

    if total <= 30:
        expl.append("Overall: LOW RISK — favorable conditions for trading")
    elif total <= 60:
        expl.append("Overall: MEDIUM RISK — mixed signals, exercise caution")
    else:
        expl.append("Overall: HIGH RISK — multiple warning signs, consider avoiding")

    return expl


def _ml_predict(symbol: str, df: pd.DataFrame, avg_sentiment: float, ind: dict) -> dict | None:
    if not os.path.exists(ML_MODEL_PATH):
        return None
    try:
        model = joblib.load(ML_MODEL_PATH)
        features = _build_feature_vector(df, avg_sentiment)
        if features is None:
            return None
        proba = model.predict_proba(features.reshape(1, -1))[0]
        pred = model.predict(features.reshape(1, -1))[0]
        return {
            "next_day_direction": "up" if pred == 1 else "down",
            "confidence": round(float(max(proba)), 3),
        }
    except Exception as e:
        logger.error(f"ML prediction failed for {symbol}: {e}")
        return None


def _build_feature_vector(df: pd.DataFrame, avg_sentiment: float) -> np.ndarray | None:
    df_ind = add_all_indicators(df)
    if df_ind.empty:
        return None
    last = df_ind.iloc[-1]
    prev = df_ind.iloc[-2] if len(df_ind) > 1 else last

    def _fv(key, default=0):
        v = last.get(key)
        return float(v) if v is not None and pd.notna(v) else default

    def _fv_prev(key, default=0):
        v = prev.get(key)
        return float(v) if v is not None and pd.notna(v) else default

    features = np.array([
        _fv("rsi", 50),
        _fv("macd_histogram", 0),
        _fv("sma_20", 0),
        _fv("sma_50", 0),
        _fv("atr", 0),
        _fv("volume_ratio", 1),
        avg_sentiment,
        _fv("stoch_rsi_k", 50),
        _fv("stoch_rsi_d", 50),
        _fv("roc", 0),
        _fv("adx", 25),
        _fv("bb_width", 0),
        _fv("obv", 0),
        _fv_prev("rsi", 50),
        _fv_prev("volume_ratio", 1),
    ])
    return features


def train_ml_model():
    symbols = ["ENGRO", "LUCK", "HBL", "OGDC", "PSO", "MARI", "SYS", "FFC", "POL", "MCB"]
    all_features = []
    all_targets = []

    saved_features, saved_targets = get_all_training_data()
    all_features.extend(saved_features)
    all_targets.extend(saved_targets)

    for symbol in symbols:
        df = psx_data.get_historical(symbol, days=730)
        if df is None or len(df) < 100:
            continue
        df = add_all_indicators(df)
        df = df.dropna().reset_index(drop=True)
        for i in range(len(df) - 1):
            row = df.iloc[i]
            next_close = df.iloc[i + 1]["close"]

            prev = df.iloc[i - 1] if i > 0 else row
            sentiment_placeholder = 0.0

            def _f(key, default=0):
                v = row.get(key)
                return float(v) if v is not None and pd.notna(v) else default

            def _fp(key, default=0):
                v = prev.get(key)
                return float(v) if v is not None and pd.notna(v) else default

            features = [
                _f("rsi", 50),
                _f("macd_histogram", 0),
                _f("sma_20", 0),
                _f("sma_50", 0),
                _f("atr", 0),
                _f("volume_ratio", 1),
                sentiment_placeholder,
                _f("stoch_rsi_k", 50),
                _f("stoch_rsi_d", 50),
                _f("roc", 0),
                _f("adx", 25),
                _f("bb_width", 0),
                _f("obv", 0),
                _fp("rsi", 50),
                _fp("volume_ratio", 1),
            ]
            all_features.append(features)
            target = 1 if float(next_close) > float(row["close"]) else 0
            all_targets.append(target)
            append_training_data(symbol, features, target)

    if len(all_features) < 100:
        logger.warning("Not enough data to train ML model")
        return

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    X = np.array(all_features)
    y = np.array(all_targets)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42)
    model.fit(X_train, y_train)
    acc = model.score(X_test, y_test)
    logger.info(f"ML model trained, accuracy: {acc:.3f}, samples: {len(X_train)}")

    os.makedirs(os.path.dirname(ML_MODEL_PATH), exist_ok=True)
    joblib.dump(model, ML_MODEL_PATH)
    logger.info(f"Model saved to {ML_MODEL_PATH}")
