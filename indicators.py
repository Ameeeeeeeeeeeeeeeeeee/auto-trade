"""
============================================================
  INDICATORS.PY — Technical Indicator Calculations (v3.0)
============================================================
  Contains functions for:
   - EMA, SMA, ATR, RSI
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands
   - Support / Resistance detection
   - Engulfing candle pattern detection
   - Hammer / Shooting Star / Doji patterns
   - Trend strength check
   - Volatility check
   - Multi-strategy signal strength scoring
============================================================
"""

import pandas as pd
import numpy as np
import config


# ──────────────────────────────────────────────
#  EMA — Exponential Moving Average
# ──────────────────────────────────────────────
def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    return data["Close"].ewm(span=period, adjust=False).mean()


# ──────────────────────────────────────────────
#  SMA — Simple Moving Average
# ──────────────────────────────────────────────
def calculate_sma(data: pd.DataFrame, period: int) -> pd.Series:
    return data["Close"].rolling(window=period).mean()


# ──────────────────────────────────────────────
#  ATR — Average True Range
# ──────────────────────────────────────────────
def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = data["High"] - data["Low"]
    high_prev_close = abs(data["High"] - data["Close"].shift(1))
    low_prev_close = abs(data["Low"] - data["Close"].shift(1))
    true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    atr = true_range.ewm(span=period, adjust=False).mean()
    return atr


# ──────────────────────────────────────────────
#  RSI — Relative Strength Index
# ──────────────────────────────────────────────
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = data["Close"].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ──────────────────────────────────────────────
#  MACD — Moving Average Convergence Divergence
# ──────────────────────────────────────────────
def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    Returns dict with 'macd_line', 'signal_line', 'histogram' as pd.Series.
    """
    ema_fast = data["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = data["Close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
    }


# ──────────────────────────────────────────────
#  BOLLINGER BANDS
# ──────────────────────────────────────────────
def calculate_bollinger_bands(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> dict:
    """
    Returns dict with 'upper', 'middle', 'lower', 'bandwidth', 'percent_b'.
    """
    middle = data["Close"].rolling(window=period).mean()
    std = data["Close"].rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    bandwidth = ((upper - lower) / middle) * 100
    percent_b = (data["Close"] - lower) / (upper - lower)
    return {
        "upper": upper,
        "middle": middle,
        "lower": lower,
        "bandwidth": bandwidth,
        "percent_b": percent_b,
    }


# ──────────────────────────────────────────────
#  SUPPORT & RESISTANCE (Pivot-Based)
# ──────────────────────────────────────────────
def find_support_resistance(data: pd.DataFrame, lookback: int = 20) -> dict:
    """
    Find recent support and resistance levels using swing highs/lows.
    """
    recent = data.tail(lookback)
    resistance = recent["High"].max()
    support = recent["Low"].min()

    # Pivot calculation
    last = data.iloc[-1]
    pivot = (last["High"] + last["Low"] + last["Close"]) / 3
    r1 = 2 * pivot - last["Low"]
    s1 = 2 * pivot - last["High"]
    r2 = pivot + (last["High"] - last["Low"])
    s2 = pivot - (last["High"] - last["Low"])

    return {
        "resistance": resistance,
        "support": support,
        "pivot": pivot,
        "r1": r1, "r2": r2,
        "s1": s1, "s2": s2,
    }


# ──────────────────────────────────────────────
#  TREND STRENGTH
# ──────────────────────────────────────────────
def check_trend_strength(ema_fast: float, ema_slow: float) -> tuple[bool, float]:
    """
    Check if the distance between EMA fast and EMA slow is strong enough.
    Returns: (is_strong, pct_distance)
    """
    if ema_slow == 0:
        return False, 0.0

    pct_distance = abs(ema_fast - ema_slow) / ema_slow * 100
    is_strong = pct_distance >= config.TREND_STRENGTH_THRESHOLD
    return is_strong, pct_distance


# ──────────────────────────────────────────────
#  VOLATILITY CHECK
# ──────────────────────────────────────────────
def check_volatility(symbol: str, current_atr: float) -> bool:
    """Check if the market activity is above the minimum ATR threshold."""
    if not config.USE_VOLATILITY_FILTER:
        return True

    threshold = config.MIN_ATR_VALUE.get(symbol, 0.0)
    return current_atr >= threshold


# ──────────────────────────────────────────────
#  CANDLE PATTERNS
# ──────────────────────────────────────────────
def is_bullish_engulfing(prev_candle: pd.Series, curr_candle: pd.Series) -> bool:
    prev_is_bearish = prev_candle["Close"] < prev_candle["Open"]
    curr_is_bullish = curr_candle["Close"] > curr_candle["Open"]
    curr_engulfs = (
        curr_candle["Open"] <= prev_candle["Close"]
        and curr_candle["Close"] >= prev_candle["Open"]
    )
    return prev_is_bearish and curr_is_bullish and curr_engulfs


def is_bearish_engulfing(prev_candle: pd.Series, curr_candle: pd.Series) -> bool:
    prev_is_bullish = prev_candle["Close"] > prev_candle["Open"]
    curr_is_bearish = curr_candle["Close"] < curr_candle["Open"]
    curr_engulfs = (
        curr_candle["Open"] >= prev_candle["Close"]
        and curr_candle["Close"] <= prev_candle["Open"]
    )
    return prev_is_bullish and curr_is_bearish and curr_engulfs


def is_hammer(candle: pd.Series, atr: float) -> bool:
    """Bullish reversal pattern — small body, long lower wick."""
    body = abs(candle["Close"] - candle["Open"])
    lower_wick = min(candle["Close"], candle["Open"]) - candle["Low"]
    upper_wick = candle["High"] - max(candle["Close"], candle["Open"])
    if body < atr * 0.1:  # doji, not hammer
        return False
    return lower_wick > body * 2 and upper_wick < body * 0.5


def is_shooting_star(candle: pd.Series, atr: float) -> bool:
    """Bearish reversal pattern — small body, long upper wick."""
    body = abs(candle["Close"] - candle["Open"])
    upper_wick = candle["High"] - max(candle["Close"], candle["Open"])
    lower_wick = min(candle["Close"], candle["Open"]) - candle["Low"]
    if body < atr * 0.1:
        return False
    return upper_wick > body * 2 and lower_wick < body * 0.5


def is_doji(candle: pd.Series, atr: float) -> bool:
    """Indecision candle — very small body relative to ATR."""
    body = abs(candle["Close"] - candle["Open"])
    return body < atr * 0.1


# ──────────────────────────────────────────────
#  MACD CROSSOVER DETECTION
# ──────────────────────────────────────────────
def detect_macd_crossover(macd_data: dict, idx: int = -2) -> str | None:
    """
    Detect MACD line crossing above/below the signal line.
    Returns 'BUY', 'SELL', or None.
    """
    try:
        macd_now = macd_data["macd_line"].iloc[idx]
        signal_now = macd_data["signal_line"].iloc[idx]
        macd_prev = macd_data["macd_line"].iloc[idx - 1]
        signal_prev = macd_data["signal_line"].iloc[idx - 1]

        # Bullish crossover: MACD crosses above signal
        if macd_prev <= signal_prev and macd_now > signal_now:
            return "BUY"
        # Bearish crossover: MACD crosses below signal
        if macd_prev >= signal_prev and macd_now < signal_now:
            return "SELL"
    except (IndexError, KeyError):
        pass
    return None


# ──────────────────────────────────────────────
#  BOLLINGER BAND SIGNAL
# ──────────────────────────────────────────────
def detect_bollinger_signal(bb_data: dict, data: pd.DataFrame, idx: int = -2) -> str | None:
    """
    Detect Bollinger Band bounce signals.
    BUY when price touches lower band and bounces.
    SELL when price touches upper band and rejects.
    """
    try:
        close = data["Close"].iloc[idx]
        prev_close = data["Close"].iloc[idx - 1]
        lower = bb_data["lower"].iloc[idx]
        upper = bb_data["upper"].iloc[idx]
        prev_lower = bb_data["lower"].iloc[idx - 1]
        prev_upper = bb_data["upper"].iloc[idx - 1]

        # Bounce from lower band (close was at/below lower, now above)
        if prev_close <= prev_lower * 1.001 and close > lower:
            return "BUY"
        # Rejection from upper band (close was at/above upper, now below)
        if prev_close >= prev_upper * 0.999 and close < upper:
            return "SELL"
    except (IndexError, KeyError):
        pass
    return None


# ──────────────────────────────────────────────
#  EMA CROSSOVER DETECTION
# ──────────────────────────────────────────────
def detect_ema_crossover(ema_fast: pd.Series, ema_slow: pd.Series, idx: int = -2) -> str | None:
    """
    Detect EMA fast crossing above/below EMA slow.
    Returns 'BUY', 'SELL', or None.
    """
    try:
        f_now = ema_fast.iloc[idx]
        s_now = ema_slow.iloc[idx]
        f_prev = ema_fast.iloc[idx - 1]
        s_prev = ema_slow.iloc[idx - 1]

        if f_prev <= s_prev and f_now > s_now:
            return "BUY"
        if f_prev >= s_prev and f_now < s_now:
            return "SELL"
    except (IndexError, KeyError):
        pass
    return None


# ──────────────────────────────────────────────
#  SIGNAL STRENGTH SCORING (MULTI-STRATEGY)
# ──────────────────────────────────────────────
def calculate_signal_strength(
    trend: str,
    pullback: bool,
    engulfing: bool,
    rsi_value: float,
    trend_strong: bool,
    volatility_strong: bool,
    ema_distance_pct: float,
    atr_value: float,
    candle_body_size: float,
    # New v3 parameters
    macd_confirms: bool = False,
    bb_confirms: bool = False,
    ema_cross_confirms: bool = False,
    candle_pattern: str = "none",
    strategies_triggered: list = None,
) -> dict:
    score = 0
    details = []

    # 1. Trend & Pullback (Core Strategy)
    if trend in ("UPTREND", "DOWNTREND") and pullback:
        score += 20
        details.append("✅ Pullback to EMA zone")

    # 2. Engulfing pattern
    if engulfing:
        score += 15
        details.append("✅ Engulfing candle confirmed")

    # 3. Trend Strength
    if trend_strong:
        score += 10
        details.append(f"✅ Strong trend ({ema_distance_pct:.2f}%)")
    else:
        details.append(f"⚠️ Weak trend ({ema_distance_pct:.2f}%)")

    # 4. RSI Confirmation
    rsi_ok = (trend == "UPTREND" and rsi_value > 50) or (trend == "DOWNTREND" and rsi_value < 50)
    if rsi_ok:
        score += 10
        details.append(f"✅ RSI confirms ({rsi_value:.1f})")
    else:
        details.append(f"🔸 RSI neutral/against ({rsi_value:.1f})")

    # 5. Volatility
    if volatility_strong:
        score += 5
        details.append("✅ Healthy volatility")
    else:
        details.append("⚠️ Low volatility")

    # 6. Candle Size vs ATR
    if atr_value > 0:
        ratio = candle_body_size / atr_value
        if ratio > 0.7:
            score += 5
            details.append("✅ Strong candle momentum")
        else:
            details.append("🔸 Average candle momentum")

    # 7. MACD Confluence (NEW)
    if macd_confirms:
        score += 15
        details.append("✅ MACD crossover confirms")

    # 8. Bollinger Band Confluence (NEW)
    if bb_confirms:
        score += 10
        details.append("✅ Bollinger Band bounce confirms")

    # 9. EMA Crossover (NEW)
    if ema_cross_confirms:
        score += 10
        details.append("✅ EMA crossover confirms")

    # 10. Candle Pattern Bonus (NEW)
    if candle_pattern == "hammer":
        score += 5
        details.append("✅ Hammer pattern (reversal)")
    elif candle_pattern == "shooting_star":
        score += 5
        details.append("✅ Shooting star (reversal)")

    # Cap at 100
    score = min(score, 100)

    # Classification
    if score >= 75:
        label, emoji = "🚀 STRONG", "💪"
    elif score >= 55:
        label, emoji = "🟡 MEDIUM", "👍"
    elif score >= 35:
        label, emoji = "🟠 MODERATE", "🔸"
    else:
        label, emoji = "🔴 WEAK", "⚠️"

    return {
        "score": score,
        "label": label,
        "emoji": emoji,
        "details": details,
    }
