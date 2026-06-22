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

logger = logging.getLogger(__name__)

ML_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "risk_classifier.pkl")


def calculate_risk(symbol: str) -> dict | None:
    df = psx_data.get_historical(symbol, days=365)
    if df is None or len(df) < 50:
        logger.warning(f"Not enough data for {symbol} to compute risk")
        return None

    ind = latest_indicators(df)
    quote = psx_data.get_quote(symbol)
    news_articles = scrape_news(symbol)

    avg_sentiment = _average_news_sentiment(news_articles)

    tech_score = _technical_score(ind, df)
    news_score = _news_score(avg_sentiment)
    vol_score = _volatility_score(df)

    total_score = tech_score * 0.50 + news_score * 0.30 + vol_score * 0.20

    total_score = max(0, min(100, total_score))

    if total_score <= 30:
        risk_level = "LOW"
    elif total_score <= 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    ml_pred = _ml_predict(symbol, df, avg_sentiment)

    explanation = _build_explanation(ind, avg_sentiment, tech_score, news_score, vol_score, total_score)

    df_with_ind = add_all_indicators(df)
    atr_pct = None
    if not df_with_ind.empty and "atr" in df_with_ind.columns:
        last = df_with_ind.iloc[-1]
        if pd.notna(last.get("atr")) and float(last.get("close", 0)) > 0:
            atr_pct = round(float(last["atr"]) / float(last["close"]) * 100, 2)

    return {
        "symbol": symbol,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "risk_score": round(total_score, 2),
        "risk_level": risk_level,
        "components": {
            "technical": round(tech_score, 2),
            "news_sentiment": round(news_score, 2),
            "volatility": round(vol_score, 2),
        },
        "indicators": {
            "rsi": ind.get("rsi"),
            "macd": ind.get("macd"),
            "sma_20": ind.get("sma_20"),
            "sma_50": ind.get("sma_50"),
            "bb_position": ind.get("bb_position"),
            "atr_percent": atr_pct,
            "volume_change": ind.get("volume_change"),
        },
        "ml_prediction": ml_pred,
        "explanation": explanation,
    }


def _technical_score(ind: dict, df: pd.DataFrame) -> float:
    score = 0.0
    max_score = 50.0

    rsi = ind.get("rsi")
    if rsi is not None:
        if rsi > 70:
            score += 10
        elif rsi < 30:
            score -= 5
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

    bb = ind.get("bb_position")
    if bb == "above":
        score += 8
    elif bb == "below":
        score -= 4

    vol_change = ind.get("volume_change")
    if vol_change is not None and vol_change > 1.5:
        score += 5
    elif vol_change is not None and vol_change < 0.5:
        score -= 2

    return max(0, min(max_score, score + 25))


def _news_score(avg_sentiment: float) -> float:
    if avg_sentiment > 0.1:
        return 5.0
    elif avg_sentiment < -0.1:
        return 25.0
    return 15.0


def _volatility_score(df: pd.DataFrame) -> float:
    if len(df) < 20:
        return 10.0
    closes = df["close"].astype(float).tail(20)
    returns = closes.pct_change().dropna()
    daily_vol = returns.std()
    annual_vol = daily_vol * np.sqrt(252)
    if annual_vol > 0.4:
        return 18.0
    elif annual_vol > 0.3:
        return 14.0
    elif annual_vol > 0.2:
        return 10.0
    else:
        return 5.0


def _average_news_sentiment(articles: list) -> float:
    if not articles:
        return 0.0
    scores = []
    for a in articles:
        text = a.get("title", "") + " " + a.get("snippet", "")
        result = analyze_sentiment(text)
        scores.append(result["compound"])
    return np.mean(scores) if scores else 0.0


def _build_explanation(ind: dict, avg_sentiment: float,
                       tech_score: float, news_score: float,
                       vol_score: float, total: float) -> list[str]:
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

    macd = ind.get("macd")
    if macd:
        expl.append(f"MACD signal — {macd.upper()}")

    bb = ind.get("bb_position")
    if bb and bb != "middle":
        expl.append(f"Price is {bb.upper()} Bollinger Bands")

    if avg_sentiment < -0.1:
        expl.append("Negative news sentiment detected")
    elif avg_sentiment > 0.1:
        expl.append("Positive news sentiment detected")
    else:
        expl.append("Neutral news sentiment")

    vol_change = ind.get("volume_change")
    if vol_change is not None and vol_change > 1.5:
        expl.append(f"Volume spike — {vol_change}x above average")

    expl.append(f"Technical score: {tech_score:.1f}/50")
    expl.append(f"News sentiment score: {news_score:.1f}/30")
    expl.append(f"Volatility score: {vol_score:.1f}/20")

    if total <= 30:
        expl.append("Overall: LOW RISK — favorable conditions for trading")
    elif total <= 60:
        expl.append("Overall: MEDIUM RISK — mixed signals, exercise caution")
    else:
        expl.append("Overall: HIGH RISK — multiple warning signs, consider avoiding")

    return expl


def _ml_predict(symbol: str, df: pd.DataFrame, avg_sentiment: float) -> dict | None:
    if not os.path.exists(ML_MODEL_PATH):
        return None
    try:
        model = joblib.load(ML_MODEL_PATH)
        df_ind = add_all_indicators(df)
        last = df_ind.iloc[-1]
        features = np.array([[
            float(last.get("rsi", 50)) if pd.notna(last.get("rsi", 50)) else 50,
            float(last.get("macd_histogram", 0)) if pd.notna(last.get("macd_histogram", 0)) else 0,
            float(last.get("sma_20", 0)) if pd.notna(last.get("sma_20", 0)) else 0,
            float(last.get("sma_50", 0)) if pd.notna(last.get("sma_50", 0)) else 0,
            float(last.get("atr", 0)) if pd.notna(last.get("atr", 0)) else 0,
            float(last.get("volume_ratio", 1)) if pd.notna(last.get("volume_ratio", 1)) else 1,
            avg_sentiment,
        ]])
        proba = model.predict_proba(features)[0]
        pred = model.predict(features)[0]
        return {
            "next_day_direction": "up" if pred == 1 else "down",
            "confidence": round(float(max(proba)), 3),
        }
    except Exception as e:
        logger.error(f"ML prediction failed for {symbol}: {e}")
        return None


def train_ml_model():
    symbols = ["ENGRO", "LUCK", "HBL", "OGDC", "PSO", "MARI", "SYS", "FFC", "POL", "MCB"]
    all_features = []
    all_targets = []

    for symbol in symbols:
        df = psx_data.get_historical(symbol, days=730)
        if df is None or len(df) < 100:
            continue
        df = add_all_indicators(df)
        df = df.dropna().reset_index(drop=True)
        for i in range(len(df) - 1):
            row = df.iloc[i]
            next_close = df.iloc[i + 1]["close"]
            features = [
                float(row.get("rsi", 50)),
                float(row.get("macd_histogram", 0)),
                float(row.get("sma_20", 0)),
                float(row.get("sma_50", 0)),
                float(row.get("atr", 0)),
                float(row.get("volume_ratio", 1)),
                0.0,
            ]
            all_features.append(features)
            all_targets.append(1 if float(next_close) > float(row["close"]) else 0)

    if len(all_features) < 100:
        logger.warning("Not enough data to train ML model")
        return

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    X = np.array(all_features)
    y = np.array(all_targets)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    acc = model.score(X_test, y_test)
    logger.info(f"ML model trained, accuracy: {acc:.3f}")

    os.makedirs(os.path.dirname(ML_MODEL_PATH), exist_ok=True)
    joblib.dump(model, ML_MODEL_PATH)
    logger.info(f"Model saved to {ML_MODEL_PATH}")
