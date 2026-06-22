import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

try:
    import psxdata
    PSXDATA_AVAILABLE = True
    logger.info("psxdata library loaded successfully")
except ImportError:
    PSXDATA_AVAILABLE = False
    logger.warning("psxdata not installed, using mock data")


def get_tickers() -> list:
    if PSXDATA_AVAILABLE:
        try:
            return psxdata.tickers()
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
    return []


def _to_float(val, default=0.0):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return float(str(val).replace("%", "").replace(",", ""))
    except (ValueError, TypeError):
        return default


def get_quote(symbol: str) -> dict | None:
    if not PSXDATA_AVAILABLE:
        return _mock_quote(symbol)
    try:
        df = psxdata.quote(symbol)
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "price": _to_float(row.get("price", 0)),
            "change": _to_float(row.get("change_pct", 0)),
            "change_percent": _to_float(row.get("change_pct", 0)),
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "volume": int(_to_float(row.get("volume_avg_30d", 0))),
            "market_cap": _to_float(row.get("market_cap")) if row.get("market_cap") is not None else None,
            "pe_ratio": _to_float(row.get("pe_ratio")) if row.get("pe_ratio") is not None else None,
        }
    except Exception as e:
        logger.error(f"Failed to fetch quote for {symbol}: {e}")
        return _mock_quote(symbol)


def get_historical(symbol: str, days: int = 365) -> pd.DataFrame | None:
    end = datetime.now()
    start = end - timedelta(days=days)
    if not PSXDATA_AVAILABLE:
        return _mock_historical(symbol, days)
    try:
        df = psxdata.stocks(
            symbol,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
        )
        if df is None or df.empty:
            logger.warning(f"No historical data for {symbol}")
            return _mock_historical(symbol, days)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {symbol}: {e}")
        return _mock_historical(symbol, days)


def _mock_quote(symbol: str) -> dict:
    import random
    base_price = {
        "ENGRO": 380, "LUCK": 950, "HBL": 120, "OGDC": 140,
        "PSO": 190, "MARI": 2100, "SYS": 550, "FFC": 160,
        "POL": 450, "MCB": 230,
    }.get(symbol, 100)
    change = round(random.uniform(-5, 5), 2)
    change_pct = round(change / base_price * 100, 2)
    return {
        "price": round(base_price + change, 2),
        "change": change,
        "change_percent": change_pct,
        "open": round(base_price + random.uniform(-3, 3), 2),
        "high": round(base_price + abs(random.uniform(0, 8)), 2),
        "low": round(base_price - abs(random.uniform(0, 8)), 2),
        "volume": random.randint(500000, 5000000),
        "market_cap": round(base_price * random.randint(50000000, 500000000), 2),
        "pe_ratio": round(random.uniform(5, 25), 2),
    }


def _mock_historical(symbol: str, days: int) -> pd.DataFrame:
    import random
    import numpy as np
    end = datetime.now()
    dates = [(end - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, 0, -1)]
    base = {"ENGRO": 380, "LUCK": 950, "HBL": 120, "OGDC": 140,
            "PSO": 190, "MARI": 2100, "SYS": 550, "FFC": 160,
            "POL": 450, "MCB": 230}.get(symbol, 100)
    price = base
    rows = []
    for d in dates:
        change_pct = random.gauss(0, 0.015)
        price = price * (1 + change_pct)
        noise = price * 0.02
        rows.append({
            "date": d,
            "open": round(price - noise + random.uniform(0, noise * 2), 2),
            "high": round(price + abs(random.gauss(0, noise)), 2),
            "low": round(price - abs(random.gauss(0, noise)), 2),
            "close": round(price, 2),
            "volume": int(abs(random.gauss(2000000, 500000))),
        })
    return pd.DataFrame(rows)
