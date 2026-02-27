"""
============================================================
  SIGNALS.PY — Multi-Strategy Trade Signal Engine (v3.0)
============================================================
  Strategies:
   1. EMA Pullback + Engulfing (original)
   2. MACD Crossover
   3. Bollinger Band Bounce
   4. EMA Crossover
   5. RSI Reversal (oversold/overbought bounce)
  
  The engine checks ALL strategies and picks the best signal
  with the highest confluence score.
============================================================
"""

import os
import csv
import pandas as pd
from datetime import datetime, timezone

from indicators import (
    calculate_ema, calculate_sma, calculate_atr, calculate_rsi,
    calculate_macd, calculate_bollinger_bands,
    find_support_resistance,
    check_trend_strength, check_volatility,
    is_bullish_engulfing, is_bearish_engulfing,
    is_hammer, is_shooting_star, is_doji,
    detect_macd_crossover, detect_bollinger_signal, detect_ema_crossover,
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
                "lot_size", "strength_score", "strength_label", "rsi", "trend", "atr", "strategy"
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
                "atr": signal["atr"],
                "strategy": signal["strategy"],
            })
    except Exception as e:
        print(f"  ⚠️ CSV Log Error: {e}")


# ──────────────────────────────────────────────
#  MARKET ANALYSIS
# ──────────────────────────────────────────────
def get_market_analysis_data(data: pd.DataFrame, symbol: str) -> dict:
    """Perform a real-time technical analysis on the provided data."""
    if len(data) < config.SLOW_EMA + 5:
        return {"error": "Not enough data for analysis"}

    ema_fast = calculate_ema(data, config.FAST_EMA)
    ema_slow = calculate_ema(data, config.SLOW_EMA)
    rsi = calculate_rsi(data, config.RSI_PERIOD)
    atr = calculate_atr(data, config.ATR_PERIOD)
    macd = calculate_macd(data)
    bb = calculate_bollinger_bands(data)

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

    # MACD Status
    macd_val = macd["macd_line"].iloc[-1]
    signal_val = macd["signal_line"].iloc[-1]
    macd_status = "Bullish" if macd_val > signal_val else "Bearish"

    # Bollinger position
    bb_pct = bb["percent_b"].iloc[-1]
    if bb_pct > 0.8: bb_status = "Near Upper Band"
    elif bb_pct < 0.2: bb_status = "Near Lower Band"
    else: bb_status = "Mid Range"

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
        "macd_status": macd_status,
        "macd_value": round(macd_val, 6),
        "bb_status": bb_status,
        "bb_percent": round(bb_pct, 3),
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M UTC")
    }


# ──────────────────────────────────────────────
#  GET DAILY SUMMARY DATA
# ──────────────────────────────────────────────
def get_daily_summary() -> dict:
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
#  STRATEGY 1: EMA PULLBACK + ENGULFING
# ──────────────────────────────────────────────
def _check_ema_pullback_engulfing(data, ema_fast, ema_slow, signal_candle, prev_candle, trend, idx):
    """Original strategy: pullback into EMA zone + engulfing candle."""
    pullback = False
    for i in range(idx - config.PULLBACK_BARS, idx + 1):
        try:
            low, high = data["Low"].iloc[i], data["High"].iloc[i]
            upper = max(ema_fast.iloc[i], ema_slow.iloc[i])
            lower = min(ema_fast.iloc[i], ema_slow.iloc[i])
            if low <= upper and high >= lower:
                pullback = True
                break
        except:
            continue

    if not pullback:
        return None

    engulfing = False
    sig_type = None
    if trend == "UPTREND" and is_bullish_engulfing(prev_candle, signal_candle):
        sig_type, engulfing = "BUY", True
    elif trend == "DOWNTREND" and is_bearish_engulfing(prev_candle, signal_candle):
        sig_type, engulfing = "SELL", True

    if sig_type:
        return {"type": sig_type, "strategy": "EMA Pullback + Engulfing", "pullback": True, "engulfing": True}
    return None


# ──────────────────────────────────────────────
#  STRATEGY 2: MACD CROSSOVER
# ──────────────────────────────────────────────
def _check_macd_crossover(macd_data, trend, curr_rsi, idx):
    """MACD line crossing signal line, confirmed by trend direction."""
    cross = detect_macd_crossover(macd_data, idx)
    if cross is None:
        return None

    # Confirm with trend direction
    if cross == "BUY" and trend == "UPTREND" and curr_rsi < 70:
        return {"type": "BUY", "strategy": "MACD Crossover", "macd_confirms": True}
    elif cross == "SELL" and trend == "DOWNTREND" and curr_rsi > 30:
        return {"type": "SELL", "strategy": "MACD Crossover", "macd_confirms": True}
    # Also allow counter-trend MACD signals with RSI confirmation
    elif cross == "BUY" and curr_rsi < 40:
        return {"type": "BUY", "strategy": "MACD Reversal", "macd_confirms": True}
    elif cross == "SELL" and curr_rsi > 60:
        return {"type": "SELL", "strategy": "MACD Reversal", "macd_confirms": True}
    return None


# ──────────────────────────────────────────────
#  STRATEGY 3: BOLLINGER BAND BOUNCE
# ──────────────────────────────────────────────
def _check_bollinger_bounce(bb_data, data, curr_rsi, idx):
    """Price bouncing off Bollinger Bands with RSI confirmation."""
    bb_signal = detect_bollinger_signal(bb_data, data, idx)
    if bb_signal is None:
        return None

    # RSI must confirm the bounce direction
    if bb_signal == "BUY" and curr_rsi < 40:
        return {"type": "BUY", "strategy": "Bollinger Bounce", "bb_confirms": True}
    elif bb_signal == "SELL" and curr_rsi > 60:
        return {"type": "SELL", "strategy": "Bollinger Bounce", "bb_confirms": True}
    return None


# ──────────────────────────────────────────────
#  STRATEGY 4: EMA CROSSOVER
# ──────────────────────────────────────────────
def _check_ema_crossover(ema_fast, ema_slow, curr_rsi, vol_ok, idx):
    """Fast EMA crossing slow EMA with volume/RSI confirmation."""
    cross = detect_ema_crossover(ema_fast, ema_slow, idx)
    if cross is None:
        return None

    if not vol_ok:
        return None

    if cross == "BUY" and curr_rsi > 45 and curr_rsi < 75:
        return {"type": "BUY", "strategy": "EMA Crossover", "ema_cross_confirms": True}
    elif cross == "SELL" and curr_rsi > 25 and curr_rsi < 55:
        return {"type": "SELL", "strategy": "EMA Crossover", "ema_cross_confirms": True}
    return None


# ──────────────────────────────────────────────
#  STRATEGY 5: RSI REVERSAL
# ──────────────────────────────────────────────
def _check_rsi_reversal(rsi_series, signal_candle, prev_candle, atr_value, idx):
    """
    RSI coming out of oversold/overbought with candle pattern confirmation.
    """
    try:
        curr_rsi = rsi_series.iloc[idx]
        prev_rsi = rsi_series.iloc[idx - 1]
    except:
        return None

    sig_type = None
    pattern = "none"

    # Oversold bounce (RSI was < 30, now crosses above 30)
    if prev_rsi < 30 and curr_rsi >= 30:
        # Confirm with bullish candle
        if signal_candle["Close"] > signal_candle["Open"]:
            sig_type = "BUY"
            if is_hammer(signal_candle, atr_value):
                pattern = "hammer"

    # Overbought rejection (RSI was > 70, now crosses below 70)
    elif prev_rsi > 70 and curr_rsi <= 70:
        if signal_candle["Close"] < signal_candle["Open"]:
            sig_type = "SELL"
            if is_shooting_star(signal_candle, atr_value):
                pattern = "shooting_star"

    if sig_type:
        return {"type": sig_type, "strategy": "RSI Reversal", "candle_pattern": pattern}
    return None


# ──────────────────────────────────────────────
#  FULL SIGNAL CHECK (MULTI-STRATEGY ENGINE)
# ──────────────────────────────────────────────
def check_signal(data: pd.DataFrame, symbol_display: str, state_mgr) -> dict | None:
    """
    Multi-strategy signal engine v3.0.
    Checks all strategies, picks the one with highest confluence.
    """
    # ── Step 1: Identify Closed Candle ──
    if len(data) < 5: return None

    signal_candle = data.iloc[-2]
    signal_timestamp = data.index[-2]
    prev_candle = data.iloc[-3]

    # ── Step 2: Prevent Duplicates ──
    if not state_mgr.is_new_candle(symbol_display, signal_timestamp):
        return None

    # ── Step 3: Cooldown & Daily Limits ──
    if state_mgr.is_in_cooldown(symbol_display):
        return None

    if state_mgr.get_daily_count(symbol_display) >= config.MAX_SIGNALS_PER_DAY:
        return None

    # ── Step 4: Enough data? ──
    min_candles = max(config.SLOW_EMA, config.MACD_SLOW, config.BB_PERIOD) + 10
    if len(data) < min_candles:
        return None

    # ── Step 5: Calculate ALL Indicators ──
    ema_fast = calculate_ema(data, config.FAST_EMA)
    ema_slow = calculate_ema(data, config.SLOW_EMA)
    atr = calculate_atr(data, config.ATR_PERIOD)
    rsi = calculate_rsi(data, config.RSI_PERIOD)
    macd = calculate_macd(data, config.MACD_FAST, config.MACD_SLOW, config.MACD_SIGNAL)
    bb = calculate_bollinger_bands(data, config.BB_PERIOD, config.BB_STD_DEV)

    idx = -2
    curr_f = ema_fast.iloc[idx]
    curr_s = ema_slow.iloc[idx]
    curr_rsi = rsi.iloc[idx]
    curr_atr = atr.iloc[idx]

    # ── Step 6: Trend & Strength Filter ──
    trend = "UPTREND" if curr_f > curr_s else "DOWNTREND"
    trend_strong, distance = check_trend_strength(curr_f, curr_s)
    vol_ok = check_volatility(symbol_display, curr_atr)

    if config.DEBUG_MODE:
        print(f"  📊 {symbol_display} [{trend}] | EMA: {distance:.3f}% | RSI: {curr_rsi:.1f} | ATR: {curr_atr:.5f} | MACD: {macd['histogram'].iloc[idx]:.5f}")

    # ── Step 7: Run ALL Strategies ──
    candidates = []

    # Strategy 1: EMA Pullback + Engulfing (needs trend strength)
    if config.STRATEGY_EMA_PULLBACK and trend_strong and vol_ok:
        result = _check_ema_pullback_engulfing(data, ema_fast, ema_slow, signal_candle, prev_candle, trend, idx)
        if result:
            # Check RSI filters
            rsi_pass = True
            if config.USE_RSI_50_CROSS:
                if trend == "UPTREND" and curr_rsi < 50: rsi_pass = False
                if trend == "DOWNTREND" and curr_rsi > 50: rsi_pass = False
            if config.USE_RSI_FILTER:
                if trend == "UPTREND" and curr_rsi > config.RSI_OVERBOUGHT: rsi_pass = False
                if trend == "DOWNTREND" and curr_rsi < config.RSI_OVERSOLD: rsi_pass = False
            if rsi_pass:
                candidates.append(result)

    # Strategy 2: MACD Crossover
    if config.STRATEGY_MACD:
        result = _check_macd_crossover(macd, trend, curr_rsi, idx)
        if result:
            candidates.append(result)

    # Strategy 3: Bollinger Band Bounce
    if config.STRATEGY_BOLLINGER:
        result = _check_bollinger_bounce(bb, data, curr_rsi, idx)
        if result:
            candidates.append(result)

    # Strategy 4: EMA Crossover
    if config.STRATEGY_EMA_CROSS:
        result = _check_ema_crossover(ema_fast, ema_slow, curr_rsi, vol_ok, idx)
        if result:
            candidates.append(result)

    # Strategy 5: RSI Reversal
    if config.STRATEGY_RSI_REVERSAL:
        result = _check_rsi_reversal(rsi, signal_candle, prev_candle, curr_atr, idx)
        if result:
            candidates.append(result)

    if not candidates:
        if config.DEBUG_MODE:
            print(f"  🔸 {symbol_display} No strategy triggered")
        return None

    # ── Step 8: Score & Pick Best ──
    best_signal = None
    best_score = -1

    for candidate in candidates:
        # Check cross-strategy confluence
        macd_cross = detect_macd_crossover(macd, idx)
        bb_sig = detect_bollinger_signal(bb, data, idx)
        ema_cross = detect_ema_crossover(ema_fast, ema_slow, idx)

        macd_confirms = (macd_cross == candidate["type"])
        bb_confirms = (bb_sig == candidate["type"])
        ema_cross_confirms = (ema_cross == candidate["type"])

        strength = calculate_signal_strength(
            trend=trend,
            pullback=candidate.get("pullback", False),
            engulfing=candidate.get("engulfing", False),
            rsi_value=curr_rsi,
            trend_strong=trend_strong,
            volatility_strong=vol_ok,
            ema_distance_pct=distance,
            atr_value=curr_atr,
            candle_body_size=abs(signal_candle["Close"] - signal_candle["Open"]),
            macd_confirms=macd_confirms,
            bb_confirms=bb_confirms,
            ema_cross_confirms=ema_cross_confirms,
            candle_pattern=candidate.get("candle_pattern", "none"),
            strategies_triggered=[c["strategy"] for c in candidates],
        )

        if strength["score"] > best_score:
            best_score = strength["score"]
            best_signal = {
                "candidate": candidate,
                "strength": strength,
            }

    # ── Step 9: Minimum Confidence Filter ──
    if best_score < config.MIN_SIGNAL_SCORE:
        if config.DEBUG_MODE:
            print(f"  ⚠️ {symbol_display} Signal too weak ({best_score}% < {config.MIN_SIGNAL_SCORE}%)")
        return None

    # ── Step 10: Build Final Signal ──
    sig_type = best_signal["candidate"]["type"]
    entry = signal_candle["Close"]
    sl = calculate_stop_loss(sig_type, entry, data, curr_atr)
    tp = calculate_take_profit(sig_type, entry, sl)
    lot = calculate_lot_size(entry, sl)
    strength = best_signal["strength"]

    # List all triggered strategies
    strategies_list = " + ".join([c["strategy"] for c in candidates])

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
        "strategy": strategies_list,
        "strategies_count": len(candidates),
        "timestamp": signal_timestamp.isoformat()
    }

    if config.DEBUG_MODE:
        print(f"  🎯 {symbol_display} [{sig_type}] via {strategies_list} (Score: {strength['score']}%)")

    # Mark this candle as processed
    state_mgr.mark_candle_processed(symbol_display, signal_timestamp)
    log_signal_to_csv(signal)
    return signal
