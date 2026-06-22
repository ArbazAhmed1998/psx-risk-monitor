import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    logger.warning("ta library not installed, using manual calculations")


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or len(df) < 50:
        return df
    df = df.copy()
    if "close" not in df.columns:
        return df
    closes = df["close"].astype(float)
    highs = df["high"].astype(float) if "high" in df.columns else closes
    lows = df["low"].astype(float) if "low" in df.columns else closes
    volumes = df["volume"].astype(float) if "volume" in df.columns else None

    if TA_AVAILABLE:
        df["rsi"] = ta.momentum.RSIIndicator(closes, window=14).rsi()
        macd = ta.trend.MACD(closes)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_histogram"] = macd.macd_diff()
        df["sma_20"] = ta.trend.SMAIndicator(closes, window=20).sma_indicator()
        df["sma_50"] = ta.trend.SMAIndicator(closes, window=50).sma_indicator()
        df["sma_200"] = ta.trend.SMAIndicator(closes, window=200).sma_indicator()
        bb = ta.volatility.BollingerBands(closes, window=20, window_dev=2)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"] = bb.bollinger_lband()
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["atr"] = ta.volatility.AverageTrueRange(highs, lows, closes, window=14).average_true_range()
        if volumes is not None:
            df["volume_sma"] = ta.trend.SMAIndicator(volumes, window=20).sma_indicator()
            df["volume_ratio"] = volumes / df["volume_sma"]
    else:
        df = _manual_indicators(df)

    df["bb_position"] = _bb_position(df)
    df["macd_signal_direction"] = _macd_signal(df)
    return df


def _manual_indicators(df: pd.DataFrame) -> pd.DataFrame:
    closes = df["close"].astype(float)
    df["rsi"] = _rsi(closes, 14)
    df["sma_20"] = closes.rolling(20).mean()
    df["sma_50"] = closes.rolling(50).mean()
    df["sma_200"] = closes.rolling(200).mean()
    macd_line = closes.ewm(span=12, adjust=False).mean() - closes.ewm(span=26, adjust=False).mean()
    df["macd"] = macd_line
    df["macd_signal"] = macd_line.ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]
    std = closes.rolling(20).std()
    sma20 = df["sma_20"]
    df["bb_upper"] = sma20 + 2 * std
    df["bb_middle"] = sma20
    df["bb_lower"] = sma20 - 2 * std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    high_low = df["high"].astype(float) - df["low"].astype(float)
    high_close = np.abs(df["high"].astype(float) - closes.shift())
    low_close = np.abs(df["low"].astype(float) - closes.shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    if "volume" in df.columns:
        volumes = df["volume"].astype(float)
        df["volume_sma"] = volumes.rolling(20).mean()
        df["volume_ratio"] = volumes / df["volume_sma"]
    return df


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _bb_position(df: pd.DataFrame) -> pd.Series:
    pos = pd.Series("middle", index=df.index)
    if "bb_upper" not in df.columns or "bb_lower" not in df.columns:
        return pos
    pos[df["close"] > df["bb_upper"]] = "above"
    pos[df["close"] < df["bb_lower"]] = "below"
    return pos


def _macd_signal(df: pd.DataFrame) -> pd.Series:
    sig = pd.Series("neutral", index=df.index)
    if "macd" not in df.columns or "macd_signal" not in df.columns:
        return sig
    sig[df["macd"] > df["macd_signal"]] = "bullish"
    sig[df["macd"] < df["macd_signal"]] = "bearish"
    return sig


def latest_indicators(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    df = add_all_indicators(df)
    last = df.iloc[-1]
    return {
        "rsi": round(float(last.get("rsi", 50)), 2) if pd.notna(last.get("rsi")) else None,
        "macd": str(last.get("macd_signal_direction", "neutral")),
        "sma_20": round(float(last.get("sma_20", 0)), 2) if pd.notna(last.get("sma_20")) else None,
        "sma_50": round(float(last.get("sma_50", 0)), 2) if pd.notna(last.get("sma_50")) else None,
        "bb_position": str(last.get("bb_position", "middle")),
        "atr_percent": round(float(last.get("atr", 0) / last.get("close", 1) * 100), 2)
        if pd.notna(last.get("atr")) and float(last.get("close", 0)) > 0 else None,
        "volume_change": round(float(last.get("volume_ratio", 1)), 2)
        if pd.notna(last.get("volume_ratio")) else None,
    }
