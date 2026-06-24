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
        df["stoch_rsi_k"] = ta.momentum.StochRSIIndicator(closes, window=14, smooth1=3, smooth2=3).stochrsi_k()
        df["stoch_rsi_d"] = ta.momentum.StochRSIIndicator(closes, window=14, smooth1=3, smooth2=3).stochrsi_d()
        df["obv"] = ta.volume.OnBalanceVolumeIndicator(closes, volumes if volumes is not None else closes).on_balance_volume()
        df["roc"] = ta.momentum.ROCIndicator(closes, window=10).roc()
        df["adx"] = ta.trend.ADXIndicator(highs, lows, closes, window=14).adx()
    else:
        df = _manual_indicators(df, closes, highs, lows, volumes)

    df["bb_position"] = _bb_position(df)
    df["macd_signal_direction"] = _macd_signal(df)
    df["sma_crossover"] = _sma_crossover(df)
    return df


def _manual_indicators(df: pd.DataFrame, closes: pd.Series, highs: pd.Series, lows: pd.Series, volumes: pd.Series | None) -> pd.DataFrame:
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
    high_low = highs - lows
    high_close = np.abs(highs - closes.shift())
    low_close = np.abs(lows - closes.shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    if volumes is not None:
        vol = volumes
        df["volume_sma"] = vol.rolling(20).mean()
        df["volume_ratio"] = vol / df["volume_sma"]
        df["obv"] = _obv(closes, vol)
    else:
        df["obv"] = 0
    df["stoch_rsi_k"], df["stoch_rsi_d"] = _stoch_rsi(closes, 14, 3, 3)
    df["roc"] = closes.pct_change(10) * 100
    df["adx"] = _adx(highs, lows, closes, 14)
    return df


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _stoch_rsi(series: pd.Series, period: int = 14, smooth_k: int = 3, smooth_d: int = 3):
    rsi = _rsi(series, period)
    min_rsi = rsi.rolling(period).min()
    max_rsi = rsi.rolling(period).max()
    stoch = 100 * (rsi - min_rsi) / (max_rsi - min_rsi).replace(0, np.nan)
    k = stoch.rolling(smooth_k).mean()
    d = k.rolling(smooth_d).mean()
    return k, d


def _obv(closes: pd.Series, volumes: pd.Series) -> pd.Series:
    obv = [0]
    for i in range(1, len(closes)):
        if closes.iloc[i] > closes.iloc[i - 1]:
            obv.append(obv[-1] + volumes.iloc[i])
        elif closes.iloc[i] < closes.iloc[i - 1]:
            obv.append(obv[-1] - volumes.iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=closes.index)


def _adx(highs: pd.Series, lows: pd.Series, closes: pd.Series, period: int = 14) -> pd.Series:
    high = highs.astype(float)
    low = lows.astype(float)
    close = closes.astype(float)
    up_move = high.diff()
    down_move = low.diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)).astype(float) * up_move
    minus_dm = ((down_move > up_move) & (down_move > 0)).astype(float) * down_move
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * plus_dm.rolling(period).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.rolling(period).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(period).mean()
    return adx


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


def _sma_crossover(df: pd.DataFrame) -> pd.Series:
    sig = pd.Series("neutral", index=df.index)
    if "sma_50" not in df.columns or "sma_200" not in df.columns:
        return sig
    sig[df["sma_50"] > df["sma_200"]] = "golden_cross"
    sig[df["sma_50"] < df["sma_200"]] = "death_cross"
    return sig


def latest_indicators(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    df = add_all_indicators(df)
    last = df.iloc[-1]

    def _v(key, default=None):
        v = last.get(key)
        if v is not None and pd.notna(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return str(v)
        return default

    def _s(key, default="neutral"):
        v = last.get(key)
        if v is not None and pd.notna(v):
            return str(v)
        return default

    close_price = _v("close", 1)
    atr_val = _v("atr")
    if atr_val is not None and close_price and close_price > 0:
        atr_pct = round(atr_val / close_price * 100, 2)
    else:
        atr_pct = None

    return {
        "rsi": _v("rsi"),
        "macd": _s("macd_signal_direction"),
        "sma_20": _v("sma_20"),
        "sma_50": _v("sma_50"),
        "bb_position": _s("bb_position"),
        "atr_percent": atr_pct,
        "volume_change": _v("volume_ratio"),
        "stoch_rsi_k": _v("stoch_rsi_k"),
        "stoch_rsi_d": _v("stoch_rsi_d"),
        "obv": _v("obv"),
        "roc": _v("roc"),
        "adx": _v("adx"),
        "sma_crossover": _s("sma_crossover"),
    }
