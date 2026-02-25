"""
============================================================
  SIGNALS.PY — Trade Signal Detection Logic (v2.0)
============================================================
  Upgraded with:
   - State management integration
   - New candle detection
   - Trend strength & Volatility filters
   - RSI 50-cross filter
   - Signal cooldown & Daily limits
   - CSV logging with rich details
============================================================
"""

import os
import csv
import pandas as pd
from datetime import datetime, timezone

from indicators import (
    calculate_ema, calculate_atr, calculate_rsi,
    check_trend_strength, check_volatility,
    is_bullish_engulfing, is_bearish_engulfing,
    calculate_signal_strength,
)
import config


# ──────────────────────────────────────────────
#  SWING HIGH / LOW
# ──────────────────────────────────────────────
def find_swing_high(data: pd.DataFrame, lookback: int = 10) -> float:
    return data["High"].iloc[-lookback:].max()


def find_swing_low(data: pd.DataFrame, lookback: int = 10) -> float:
    return data["Low"].iloc[-lookback:].min()


# ──────────────────────────────────────────────
#  STOP LOSS CALCULATION
# ──────────────────────────────────────────────
def calculate_stop_loss(direction: str, entry: float, data: pd.DataFrame, atr_value: float) -> float:
    if config.SL_MODE == 0:
        if direction == "BUY":
            sl = find_swing_low(data, config.SWING_LOOKBACK)
        else:
            sl = find_swing_high(data, config.SWING_LOOKBACK)
    else:
        distance = atr_value * config.ATR_MULTIPLIER
        sl = entry - distance if direction == "BUY" else entry + distance
    return round(sl, 5)


# ──────────────────────────────────────────────
#  TAKE PROFIT CALCULATION
# ──────────────────────────────────────────────
def calculate_take_profit(direction: str, entry: float, sl: float) -> float:
    sl_distance = abs(entry - sl)
    tp_distance = sl_distance * config.RISK_REWARD
    tp = entry + tp_distance if direction == "BUY" else entry - tp_distance
    return round(tp, 5)


# ──────────────────────────────────────────────
#  LOT SIZE CALCULATION
# ──────────────────────────────────────────────
def calculate_lot_size(entry: float, sl: float) -> float:
    if config.USE_FIXED_LOT:
        return config.FIXED_LOT_SIZE
    risk_amount = config.ACCOUNT_BALANCE * (config.RISK_PERCENT / 100)
    sl_distance = abs(entry - sl)
    if sl_distance == 0: return config.FIXED_LOT_SIZE
    lot_size = risk_amount / (sl_distance * 100000)
    return max(round(lot_size, 2), 0.01)


# ──────────────────────────────────────────────
#  LOG SIGNAL TO CSV
# ──────────────────────────────────────────────
def log_signal_to_csv(signal: dict):
    if not config.LOG_SIGNALS_TO_CSV: return
    file_exists = os.path.exists(config.SIGNAL_LOG_FILE)
    try:
        with open(config.SIGNAL_LOG_FILE, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "symbol", "type", "entry", "stop_loss", "take_profit",
                "lot_size", "strength_score", "strength_label", "rsi", "trend", "atr"
            ])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": signal["symbol"],
                "type": signal["type"],
                "entry": signal["entry"],
                "stop_loss": signal["stop_loss"],
                "take_profit": signal["take_profit"],
                "lot_size": signal["lot_size"],
                "strength_score": signal["strength_score"],
                "strength_label": signal["strength_label"],
                "rsi": signal["rsi"],
                "trend": signal["trend"],
                "atr": signal["atr"]
            })
    except Exception as e:
        print(f"  ⚠️ CSV Log Error: {e}")


# ──────────────────────────────────────────────
#  MARKET ANALYSIS (NEW)
# ──────────────────────────────────────────────
def get_market_analysis_data(data: pd.DataFrame, symbol: str) -> dict:
    """
    Perform a real-time technical analysis on the provided data.
    """
    if len(data) < config.SLOW_EMA + 5:
        return {"error": "Not enough data for analysis"}

    ema_fast = calculate_ema(data, config.FAST_EMA)
    ema_slow = calculate_ema(data, config.SLOW_EMA)
    rsi = calculate_rsi(data, config.RSI_PERIOD)
    atr = calculate_atr(data, config.ATR_PERIOD)
    
    curr_f = ema_fast.iloc[-1]
    curr_s = ema_slow.iloc[-1]
    curr_rsi = rsi.iloc[-1]
    curr_atr = atr.iloc[-1]
    price = data["Close"].iloc[-1]
    
    trend = "UPTREND" if curr_f > curr_s else "DOWNTREND"
    trend_strong, distance = check_trend_strength(curr_f, curr_s)
    
    # RSI Condition
    rsi_status = "Neutral"
    if curr_rsi > 70: rsi_status = "Overbought"
    elif curr_rsi < 30: rsi_status = "Oversold"
    elif curr_rsi > 50: rsi_status = "Bullish Bias"
    elif curr_rsi < 50: rsi_status = "Bearish Bias"

    return {
        "symbol": symbol,
        "price": round(price, 5),
        "trend": trend,
        "trend_strength": "STRONG" if trend_strong else "WEAK/SIDEWAYS",
        "ema_separation": round(distance, 4),
        "rsi": round(curr_rsi, 2),
        "rsi_status": rsi_status,
        "atr": round(curr_atr, 6),
        "volatility": "High" if check_volatility(symbol, curr_atr) else "Low/Stable",
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M UTC")
    }


# ──────────────────────────────────────────────
#  GET DAILY SUMMARY DATA
# ──────────────────────────────────────────────
def get_daily_summary() -> dict:
    """
    Read today's signals from the CSV log and compile a summary.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary = {
        "date": today,
        "total_signals": 0,
        "buy_signals": 0,
        "sell_signals": 0,
        "symbols_traded": set(),
        "signals": [],
    }

    if not os.path.exists(config.SIGNAL_LOG_FILE):
        return summary

    try:
        with open(config.SIGNAL_LOG_FILE, mode="r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["timestamp"].startswith(today):
                    summary["total_signals"] += 1
                    if row["type"] == "BUY":
                        summary["buy_signals"] += 1
                    else:
                        summary["sell_signals"] += 1
                    summary["symbols_traded"].add(row["symbol"])
                    summary["signals"].append(row)
    except Exception as e:
        print(f"  ⚠️ Error reading signal log: {e}")

    summary["symbols_traded"] = list(summary["symbols_traded"])
    return summary


# ──────────────────────────────────────────────
#  FULL SIGNAL CHECK (ADVANCED)
# ──────────────────────────────────────────────
def check_signal(data: pd.DataFrame, symbol_display: str, state_mgr) -> dict | None:
    """
    Main signal logic with all v2.0 upgrades.
    """
    # ── Step 1: Identify Closed Candle ──
    # Usually yfinance last row is live. We want the latest CLOSED candle.
    # We will treat data.iloc[-2] as the signal candle (the one that just closed).
    if len(data) < 5: return None
    
    signal_candle = data.iloc[-2]
    signal_timestamp = data.index[-2]
    prev_candle = data.iloc[-3]
    
    # ── Step 2: Prevent Duplicates (Already sent for this closed candle?) ──
    if not state_mgr.is_new_candle(symbol_display, signal_timestamp):
        return None

    # ── Step 3: Cooldown & Daily Limits ──
    if state_mgr.is_in_cooldown(symbol_display):
        return None
    
    if state_mgr.get_daily_count(symbol_display) >= config.MAX_SIGNALS_PER_DAY:
        return None

    # ── Step 4: Enough data for indicators? ──
    min_candles = config.SLOW_EMA + 10
    if len(data) < min_candles:
        return None

    # ── Step 5: Calculate Indicators ──
    ema_fast = calculate_ema(data, config.FAST_EMA)
    ema_slow = calculate_ema(data, config.SLOW_EMA)
    atr = calculate_atr(data, config.ATR_PERIOD)
    rsi = calculate_rsi(data, config.RSI_PERIOD)
    
    # Use values from the signal candle (iloc[-2])
    idx = -2
    curr_f = ema_fast.iloc[idx]
    curr_s = ema_slow.iloc[idx]
    curr_rsi = rsi.iloc[idx]
    curr_atr = atr.iloc[idx]
    
    # ── Step 6: Trend & Strength Filter ──
    trend = "UPTREND" if curr_f > curr_s else "DOWNTREND"
    trend_strong, distance = check_trend_strength(curr_f, curr_s)
    
    if config.DEBUG_MODE:
        print(f"  📊 {symbol_display} [{trend}] | EMA Sep: {distance:.3f}% | RSI: {curr_rsi:.1f} | ATR: {curr_atr:.5f}")

    if not trend_strong:
        if config.DEBUG_MODE: print(f"  🥱 {symbol_display} Trend too weak ({distance:.2f}%)")
        return None

    # ── Step 7: RSI 50 Filter (NEW) ──
    if config.USE_RSI_50_CROSS:
        if trend == "UPTREND" and curr_rsi < 50:
            if config.DEBUG_MODE: print(f"  ⚠️ {symbol_display} RSI below 50 in Uptrend")
            return None
        if trend == "DOWNTREND" and curr_rsi > 50:
            if config.DEBUG_MODE: print(f"  ⚠️ {symbol_display} RSI above 50 in Downtrend")
            return None

    # ── Step 8: Overbought/Oversold Filter ──
    if config.USE_RSI_FILTER:
        if trend == "UPTREND" and curr_rsi > config.RSI_OVERBOUGHT:
            if config.DEBUG_MODE: print(f"  ⚠️ {symbol_display} Overbought")
            return None
        if trend == "DOWNTREND" and curr_rsi < config.RSI_OVERSOLD:
            if config.DEBUG_MODE: print(f"  ⚠️ {symbol_display} Oversold")
            return None

    # ── Step 9: Volatility Filter (NEW) ──
    vol_ok = check_volatility(symbol_display, curr_atr)
    if not vol_ok:
        if config.DEBUG_MODE: print(f"  💤 {symbol_display} Low Volatility (ATR: {curr_atr:.5f})")
        return None

    # ── Step 10: Pullback ──
    pullback = False
    # Check if any of the last few candles touched the zone
    for i in range(idx - config.PULLBACK_BARS, idx + 1):
        try:
            low, high = data["Low"].iloc[i], data["High"].iloc[i]
            upper = max(ema_fast.iloc[i], ema_slow.iloc[i])
            lower = min(ema_fast.iloc[i], ema_slow.iloc[i])
            if low <= upper and high >= lower:
                pullback = True
                break
        except: continue
        
    if not pullback:
        if config.DEBUG_MODE: print(f"  🔍 {symbol_display} No pullback in EMA zone")
        return None

    # ── Step 11: Engulfing on Signal Candle ──
    sig_type = None
    engulfing = False
    
    if trend == "UPTREND" and is_bullish_engulfing(prev_candle, signal_candle):
        sig_type, engulfing = "BUY", True
    elif trend == "DOWNTREND" and is_bearish_engulfing(prev_candle, signal_candle):
        sig_type, engulfing = "SELL", True
        
    if not sig_type:
        if config.DEBUG_MODE: print(f"  🔸 {symbol_display} No engulfing pattern")
        return None

    # ── Step 12: Final Signal Construction ──
    entry = signal_candle["Close"]
    sl = calculate_stop_loss(sig_type, entry, data, curr_atr)
    tp = calculate_take_profit(sig_type, entry, sl)
    lot = calculate_lot_size(entry, sl)
    
    strength = calculate_signal_strength(
        trend=trend, pullback=pullback, engulfing=engulfing,
        rsi_value=curr_rsi, trend_strong=trend_strong,
        volatility_strong=vol_ok, ema_distance_pct=distance,
        atr_value=curr_atr, candle_body_size=abs(signal_candle["Close"] - signal_candle["Open"])
    )

    signal = {
        "type": sig_type,
        "symbol": symbol_display,
        "entry": round(entry, 5),
        "stop_loss": sl,
        "take_profit": tp,
        "lot_size": lot,
        "trend": trend,
        "rsi": round(curr_rsi, 1),
        "atr": round(curr_atr, 6),
        "strength_score": strength["score"],
        "strength_label": strength["label"],
        "strength_emoji": strength["emoji"],
        "strength_details": strength["details"],
        "strategy": "EMA Pullback + Engulfing",
        "timestamp": signal_timestamp.isoformat()
    }

    # Mark this candle as officially "processed" and "signal sent"
    state_mgr.mark_candle_processed(symbol_display, signal_timestamp)
    log_signal_to_csv(signal)
    return signal
