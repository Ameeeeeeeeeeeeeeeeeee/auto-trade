"""
============================================================
  CHART_ANALYSIS.PY — Chart Generation & Deep Word Analysis
============================================================
  Features:
   - Professional candlestick chart with EMA overlays
   - RSI subplot with zones
   - Volume bars with color coding
   - Deep word-based market analysis (support/resistance,
     momentum, trend commentary, actionable recommendation)
============================================================
"""

import os
import io
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import mplfinance as mpf

from indicators import (
    calculate_ema, calculate_atr, calculate_rsi,
    check_trend_strength, check_volatility,
)
import config


# ──────────────────────────────────────────────
#  CHART STYLE — Custom dark theme
# ──────────────────────────────────────────────
CHART_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(
        up="#00e676",        # green candles
        down="#ff1744",      # red candles
        edge="inherit",
        wick="inherit",
        volume={"up": "#00e67644", "down": "#ff174444"},
    ),
    facecolor="#0d1117",
    edgecolor="#21262d",
    figcolor="#0d1117",
    gridcolor="#21262d",
    gridstyle="--",
    rc={
        "font.size": 9,
        "axes.labelcolor": "#8b949e",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
    },
)


# ──────────────────────────────────────────────
#  GENERATE CHART IMAGE
# ──────────────────────────────────────────────
def generate_chart(data: pd.DataFrame, symbol: str, num_candles: int = 60) -> str | None:
    """
    Generate a professional candlestick chart and return the file path.
    Includes: EMA 20/50, RSI subplot, Volume bars.
    Returns the path to the saved PNG image, or None on error.
    """
    try:
        # Trim to last N candles
        df = data.tail(num_candles).copy()

        # Calculate indicators
        ema_fast = calculate_ema(data, config.FAST_EMA).tail(num_candles)
        ema_slow = calculate_ema(data, config.SLOW_EMA).tail(num_candles)
        rsi = calculate_rsi(data, config.RSI_PERIOD).tail(num_candles)

        # Prepare additional plots (EMA lines)
        add_plots = [
            mpf.make_addplot(ema_fast, color="#42a5f5", width=1.2, label=f"EMA {config.FAST_EMA}"),
            mpf.make_addplot(ema_slow, color="#ffa726", width=1.2, label=f"EMA {config.SLOW_EMA}"),
            # RSI in a separate panel
            mpf.make_addplot(rsi, panel=2, color="#ab47bc", width=1.0, ylabel="RSI"),
            mpf.make_addplot(
                pd.Series([70] * len(df), index=df.index),
                panel=2, color="#ff174488", linestyle="--", width=0.6,
            ),
            mpf.make_addplot(
                pd.Series([30] * len(df), index=df.index),
                panel=2, color="#00e67688", linestyle="--", width=0.6,
            ),
            mpf.make_addplot(
                pd.Series([50] * len(df), index=df.index),
                panel=2, color="#8b949e44", linestyle=":", width=0.5,
            ),
        ]

        # Create a temp file for the chart
        tmp_path = os.path.join(tempfile.gettempdir(), f"chart_{symbol}_{int(datetime.now().timestamp())}.png")

        # Generate the chart
        fig, axes = mpf.plot(
            df,
            type="candle",
            style=CHART_STYLE,
            addplot=add_plots,
            volume=True,
            volume_panel=1,
            panel_ratios=(5, 1.5, 2),
            figsize=(12, 8),
            tight_layout=True,
            returnfig=True,
        )

        # Title
        fig.suptitle(
            f"📊 {symbol}  |  {config.TIMEFRAME}  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            fontsize=14,
            fontweight="bold",
            color="#e6edf3",
            y=0.98,
        )

        # Add EMA legend to price panel
        price_ax = axes[0]
        price_ax.legend(
            [f"EMA {config.FAST_EMA}", f"EMA {config.SLOW_EMA}"],
            loc="upper left",
            fontsize=8,
            facecolor="#0d1117",
            edgecolor="#30363d",
            labelcolor="#e6edf3",
        )

        # Add RSI label
        rsi_ax = axes[4]  # RSI panel axis
        rsi_ax.set_ylabel("RSI", fontsize=9, color="#ab47bc")
        rsi_ax.set_ylim(0, 100)

        # Save
        fig.savefig(tmp_path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
        plt.close(fig)

        return tmp_path

    except Exception as e:
        print(f"  ⚠️ Chart Generation Error: {e}")
        return None


# ──────────────────────────────────────────────
#  DEEP WORD-BASED ANALYSIS
# ──────────────────────────────────────────────
def generate_deep_analysis(data: pd.DataFrame, symbol: str) -> dict | None:
    """
    Produce a comprehensive word-based technical analysis.
    Returns a dict with all analysis fields, or None on error.
    """
    try:
        if len(data) < config.SLOW_EMA + 10:
            return {"error": "Not enough data for deep analysis."}

        # ── Calculate indicators ──
        ema_fast = calculate_ema(data, config.FAST_EMA)
        ema_slow = calculate_ema(data, config.SLOW_EMA)
        rsi = calculate_rsi(data, config.RSI_PERIOD)
        atr = calculate_atr(data, config.ATR_PERIOD)

        price = data["Close"].iloc[-1]
        curr_f = ema_fast.iloc[-1]
        curr_s = ema_slow.iloc[-1]
        curr_rsi = rsi.iloc[-1]
        curr_atr = atr.iloc[-1]

        # ── Trend Analysis ──
        trend = "UPTREND" if curr_f > curr_s else "DOWNTREND"
        trend_strong, distance = check_trend_strength(curr_f, curr_s)
        vol_ok = check_volatility(symbol, curr_atr)

        # ── Support & Resistance ──
        lookback = min(50, len(data))
        recent = data.tail(lookback)
        resistance = recent["High"].max()
        support = recent["Low"].min()

        # Intermediate S/R (pivot points)
        pivot = (recent["High"].iloc[-1] + recent["Low"].iloc[-1] + recent["Close"].iloc[-1]) / 3
        r1 = 2 * pivot - recent["Low"].iloc[-1]
        s1 = 2 * pivot - recent["High"].iloc[-1]

        # ── Momentum ──
        price_change_5 = ((price - data["Close"].iloc[-6]) / data["Close"].iloc[-6]) * 100 if len(data) >= 6 else 0
        price_change_20 = ((price - data["Close"].iloc[-21]) / data["Close"].iloc[-21]) * 100 if len(data) >= 21 else 0

        # ── Volume Analysis ──
        avg_vol = data["Volume"].tail(20).mean() if "Volume" in data.columns else 0
        curr_vol = data["Volume"].iloc[-1] if "Volume" in data.columns else 0
        vol_ratio = (curr_vol / avg_vol) if avg_vol > 0 else 1.0

        # ── RSI Divergence (simple check) ──
        rsi_5_ago = rsi.iloc[-6] if len(rsi) >= 6 else curr_rsi
        price_5_ago = data["Close"].iloc[-6] if len(data) >= 6 else price
        bullish_div = (price < price_5_ago) and (curr_rsi > rsi_5_ago)
        bearish_div = (price > price_5_ago) and (curr_rsi < rsi_5_ago)

        # ── Candle Pattern ──
        last_candle = data.iloc[-1]
        body = abs(last_candle["Close"] - last_candle["Open"])
        upper_wick = last_candle["High"] - max(last_candle["Close"], last_candle["Open"])
        lower_wick = min(last_candle["Close"], last_candle["Open"]) - last_candle["Low"]
        candle_type = "Bullish" if last_candle["Close"] > last_candle["Open"] else "Bearish"

        # Doji detection
        is_doji = body < curr_atr * 0.1
        # Hammer
        is_hammer = (lower_wick > body * 2) and (upper_wick < body * 0.5) and not is_doji
        # Shooting star
        is_shooting_star = (upper_wick > body * 2) and (lower_wick < body * 0.5) and not is_doji

        candle_pattern = "None"
        if is_doji:
            candle_pattern = "Doji (Indecision)"
        elif is_hammer:
            candle_pattern = "Hammer (Potential Reversal Up)"
        elif is_shooting_star:
            candle_pattern = "Shooting Star (Potential Reversal Down)"

        # ── Build Narrative ──
        # Trend commentary
        if trend == "UPTREND" and trend_strong:
            trend_narrative = f"📈 {symbol} is in a **STRONG UPTREND**. The fast EMA ({config.FAST_EMA}) is clearly above the slow EMA ({config.SLOW_EMA}) with {distance:.3f}% separation, signaling firm bullish control."
        elif trend == "UPTREND":
            trend_narrative = f"📈 {symbol} shows an uptrend, but the EMA separation is narrow ({distance:.3f}%). This suggests the trend is weak or potentially transitioning — exercise caution."
        elif trend == "DOWNTREND" and trend_strong:
            trend_narrative = f"📉 {symbol} is in a **STRONG DOWNTREND**. The fast EMA is decisively below the slow EMA by {distance:.3f}%, indicating bears are in control."
        else:
            trend_narrative = f"📉 {symbol} shows a downtrend, but the EMAs are very close ({distance:.3f}%). The market may be consolidating or preparing for a reversal."

        # RSI commentary
        if curr_rsi > 70:
            rsi_narrative = f"🔴 RSI is at {curr_rsi:.1f} — **OVERBOUGHT** territory. Price may be exhausted. Watch for reversal or pullback signals."
        elif curr_rsi > 60:
            rsi_narrative = f"🟢 RSI at {curr_rsi:.1f} shows strong bullish momentum, but approaching overbought. Still room for upside."
        elif curr_rsi > 50:
            rsi_narrative = f"🟢 RSI at {curr_rsi:.1f} indicates mild bullish bias. Momentum slightly favors buyers."
        elif curr_rsi > 40:
            rsi_narrative = f"🔸 RSI at {curr_rsi:.1f} is neutral-bearish. Neither buyers nor sellers have strong conviction."
        elif curr_rsi > 30:
            rsi_narrative = f"🔴 RSI at {curr_rsi:.1f} indicates bearish momentum. Sellers are gaining traction."
        else:
            rsi_narrative = f"🟢 RSI is at {curr_rsi:.1f} — **OVERSOLD** territory. A bounce or reversal could be imminent."

        # Volatility commentary
        if vol_ok:
            vol_narrative = f"📊 ATR ({curr_atr:.5f}) is above minimum threshold — the market has **healthy volatility** for trading."
        else:
            vol_narrative = f"💤 ATR ({curr_atr:.5f}) is below the minimum threshold — market is in a **low-volatility state**. Avoid entering trades until activity picks up."

        # Volume commentary
        if vol_ratio > 1.5:
            volume_narrative = f"🔊 Volume is {vol_ratio:.1f}x above average — **high activity** suggests strong conviction in the current move."
        elif vol_ratio > 0.8:
            volume_narrative = f"📢 Volume is near average ({vol_ratio:.1f}x) — normal market participation."
        else:
            volume_narrative = f"🔇 Volume is {vol_ratio:.1f}x below average — **low participation** could indicate a lack of conviction."

        # Divergence commentary
        div_narrative = ""
        if bullish_div:
            div_narrative = "⚡ **Bullish RSI Divergence** detected: Price made a lower low but RSI made a higher low. This can precede a reversal upward."
        elif bearish_div:
            div_narrative = "⚡ **Bearish RSI Divergence** detected: Price made a higher high but RSI made a lower high. This can signal a coming downturn."

        # Recommendation
        if trend == "UPTREND" and trend_strong and 40 < curr_rsi < 70 and vol_ok:
            recommendation = "✅ **BUY BIAS** — Conditions favor long entries. Look for pullbacks to the EMA zone for optimal entry."
            rec_emoji = "🟢"
        elif trend == "DOWNTREND" and trend_strong and 30 < curr_rsi < 60 and vol_ok:
            recommendation = "✅ **SELL BIAS** — Conditions favor short entries. Look for rallies into the EMA zone for optimal entry."
            rec_emoji = "🔴"
        elif curr_rsi > 70:
            recommendation = "⚠️ **CAUTION** — Overbought conditions. Avoid new longs. Watch for short setups on reversal signals."
            rec_emoji = "⚠️"
        elif curr_rsi < 30:
            recommendation = "⚠️ **CAUTION** — Oversold conditions. Avoid new shorts. Watch for long setups on reversal signals."
            rec_emoji = "⚠️"
        elif not trend_strong:
            recommendation = "🔸 **WAIT** — Trend is weak / market is sideways. Best to stay on the sidelines until a clear direction emerges."
            rec_emoji = "⏸️"
        elif not vol_ok:
            recommendation = "💤 **WAIT** — Low volatility. Market is too quiet. Wait for a breakout with volume confirmation."
            rec_emoji = "⏸️"
        else:
            recommendation = "🔸 **NEUTRAL** — Mixed signals. No clear edge. Wait for confluences to align."
            rec_emoji = "⏸️"

        return {
            "symbol": symbol,
            "price": round(price, 5),
            "trend": trend,
            "trend_strength": "STRONG" if trend_strong else "WEAK",
            "ema_separation": round(distance, 4),
            "ema_fast_val": round(curr_f, 5),
            "ema_slow_val": round(curr_s, 5),
            "rsi": round(curr_rsi, 2),
            "atr": round(curr_atr, 6),
            "volatility_ok": vol_ok,
            "support": round(support, 5),
            "resistance": round(resistance, 5),
            "pivot": round(pivot, 5),
            "r1": round(r1, 5),
            "s1": round(s1, 5),
            "price_change_5": round(price_change_5, 2),
            "price_change_20": round(price_change_20, 2),
            "vol_ratio": round(vol_ratio, 2),
            "candle_type": candle_type,
            "candle_pattern": candle_pattern,
            "bullish_divergence": bullish_div,
            "bearish_divergence": bearish_div,
            # Narratives
            "trend_narrative": trend_narrative,
            "rsi_narrative": rsi_narrative,
            "vol_narrative": vol_narrative,
            "volume_narrative": volume_narrative,
            "div_narrative": div_narrative,
            "recommendation": recommendation,
            "rec_emoji": rec_emoji,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

    except Exception as e:
        print(f"  ⚠️ Deep Analysis Error: {e}")
        return {"error": str(e)}


# ──────────────────────────────────────────────
#  FORMAT DEEP ANALYSIS MESSAGE
# ──────────────────────────────────────────────
def format_deep_analysis_message(analysis: dict) -> str:
    """
    Format the deep analysis into a rich Telegram message.
    """
    if "error" in analysis:
        return f"❌ {analysis['error']}"

    msg = (
        f"<b>🧠 DEEP MARKET ANALYSIS</b>\n"
        f"<b>{'━' * 28}</b>\n"
        f"📍 <b>{analysis['symbol']}</b>  |  💵 <code>{analysis['price']}</code>\n"
        f"🕒 <i>{analysis['timestamp']}</i>\n\n"

        f"<b>📈 TREND ANALYSIS</b>\n"
        f"{'━' * 28}\n"
        f"{analysis['trend_narrative']}\n\n"

        f"• EMA {config.FAST_EMA}: <code>{analysis['ema_fast_val']}</code>\n"
        f"• EMA {config.SLOW_EMA}: <code>{analysis['ema_slow_val']}</code>\n"
        f"• Separation: <code>{analysis['ema_separation']}%</code>\n\n"

        f"<b>💠 RSI MOMENTUM</b>\n"
        f"{'━' * 28}\n"
        f"{analysis['rsi_narrative']}\n\n"

        f"<b>📊 VOLATILITY & VOLUME</b>\n"
        f"{'━' * 28}\n"
        f"{analysis['vol_narrative']}\n"
        f"{analysis['volume_narrative']}\n\n"

        f"<b>🏗️ KEY LEVELS</b>\n"
        f"{'━' * 28}\n"
        f"🔴 Resistance: <code>{analysis['resistance']}</code>\n"
        f"🔵 R1 Pivot:   <code>{analysis['r1']}</code>\n"
        f"⚪ Pivot:       <code>{analysis['pivot']}</code>\n"
        f"🔵 S1 Pivot:   <code>{analysis['s1']}</code>\n"
        f"🟢 Support:    <code>{analysis['support']}</code>\n\n"

        f"<b>📉 PRICE CHANGE</b>\n"
        f"{'━' * 28}\n"
        f"• Last 5 candles: <code>{analysis['price_change_5']:+.2f}%</code>\n"
        f"• Last 20 candles: <code>{analysis['price_change_20']:+.2f}%</code>\n\n"

        f"<b>🕯️ CANDLE INFO</b>\n"
        f"{'━' * 28}\n"
        f"• Type: {analysis['candle_type']}\n"
        f"• Pattern: {analysis['candle_pattern']}\n"
    )

    if analysis["div_narrative"]:
        msg += f"\n{analysis['div_narrative']}\n"

    msg += (
        f"\n<b>{analysis['rec_emoji']} RECOMMENDATION</b>\n"
        f"{'━' * 28}\n"
        f"{analysis['recommendation']}\n\n"
        f"⚠️ <i>This is not financial advice. Trade at your own risk!</i>"
    )

    return msg
