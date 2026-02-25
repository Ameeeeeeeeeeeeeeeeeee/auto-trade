"""
============================================================
  INDICATORS.PY — Technical Indicator Calculations (v2.0)
============================================================
  Contains functions for:
   - EMA, ATR, RSI
   - Engulfing candle pattern detection
   - Trend strength check — NEW
   - Volatility check — NEW
   - Signal strength scoring
============================================================
"""

import pandas as pd
import config


# ──────────────────────────────────────────────
#  EMA — Exponential Moving Average
# ──────────────────────────────────────────────
def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    return data["Close"].ewm(span=period, adjust=False).mean()


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
#  TREND STRENGTH (NEW)
# ──────────────────────────────────────────────
def check_trend_strength(ema_fast: float, ema_slow: float) -> tuple[bool, float]:
    """
    Check if the distance between EMA 20 and EMA 50 is strong enough.
    Returns: (is_strong, pct_distance)
    """
    if ema_slow == 0:
        return False, 0.0
    
    pct_distance = abs(ema_fast - ema_slow) / ema_slow * 100
    is_strong = pct_distance >= config.TREND_STRENGTH_THRESHOLD
    return is_strong, pct_distance


# ──────────────────────────────────────────────
#  VOLATILITY CHECK (NEW)
# ──────────────────────────────────────────────
def check_volatility(symbol: str, current_atr: float) -> bool:
    """Check if the market activity is above the minimum ATR threshold."""
    if not config.USE_VOLATILITY_FILTER:
        return True
    
    threshold = config.MIN_ATR_VALUE.get(symbol, 0.0)
    return current_atr >= threshold


# ──────────────────────────────────────────────
#  ENGULFING CANDLE PATTERNS
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


# ──────────────────────────────────────────────
#  SIGNAL STRENGTH SCORING
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
) -> dict:
    score = 0
    details = []

    # 1. Trend & Pullback (Core Strategy)
    if trend in ("UPTREND", "DOWNTREND") and pullback:
        score += 30
        details.append("✅ Strategy conditions met")

    # 2. Engulfing pattern
    if engulfing:
        score += 20
        details.append("✅ Engulfing candle confirmed")

    # 3. Trend Strength
    if trend_strong:
        score += 15
        details.append(f"✅ Strong trend ({ema_distance_pct:.2f}%)")
    else:
        details.append(f"⚠️ Weak trend ({ema_distance_pct:.2f}%)")

    # 4. RSI Confirmation
    # RSI > 50 for BUY, RSI < 50 for SELL is extra confirmation
    rsi_ok = (trend == "UPTREND" and rsi_value > 50) or (trend == "DOWNTREND" and rsi_value < 50)
    if rsi_ok:
        score += 15
        details.append(f"✅ RSI confirms ({rsi_value:.1f})")
    else:
        details.append(f"🔸 RSI neutral/against ({rsi_value:.1f})")

    # 5. Volatility
    if volatility_strong:
        score += 10
        details.append("✅ Market volatility healthy")
    else:
        details.append("⚠️ Low market volatility")

    # 6. Candle Size vs ATR
    if atr_value > 0:
        ratio = candle_body_size / atr_value
        if ratio > 0.7:
            score += 10
            details.append("✅ Strong candle momentum")
        else:
            details.append("🔸 Average candle momentum")

    # Classification
    if score >= 80:
        label, emoji = "🚀 STRONG", "💪"
    elif score >= 60:
        label, emoji = "🟡 MEDIUM", "👍"
    else:
        label, emoji = "🔴 WEAK", "⚠️"

    return {
        "score": score,
        "label": label,
        "emoji": emoji,
        "details": details,
    }
