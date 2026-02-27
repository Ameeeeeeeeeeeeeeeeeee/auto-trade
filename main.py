"""
============================================================
  MAIN.PY — Multi-Strategy Trading Bot v3.0
============================================================
  Features:
   - 5 Trading Strategies running in parallel
   - Persistence (Bot state survives restart)
   - Interactive Telegram Commands
   - Chart & Deep Analysis
   - Multi-Symbol Scan
   - Railway / Cloud deployment ready
============================================================
"""

import time
import logging
from datetime import datetime, timezone

import yfinance as yf
import pandas as pd

import config
from signals import check_signal, get_daily_summary, get_market_analysis_data
from telegram_bot import broadcast_signal, broadcast_message, send_daily_summary, handle_commands
from state_manager import StateManager


# ──────────────────────────────────────────────
#  LOGGING SETUP
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  FETCH DATA
# ──────────────────────────────────────────────
def fetch_data(ticker: str, display_name: str) -> pd.DataFrame | None:
    try:
        data = yf.download(
            tickers=ticker,
            period=config.DATA_PERIOD,
            interval=config.TIMEFRAME,
            progress=False,
        )
        if data is None or data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        logger.error(f"Error fetching {display_name}: {e}")
        return None


# ──────────────────────────────────────────────
#  TRADING HOURS CHECK
# ──────────────────────────────────────────────
def is_trading_hours() -> bool:
    if config.TRADE_START_HOUR == 0 and config.TRADE_END_HOUR == 24:
        return True
    current_hour = datetime.now(timezone.utc).hour
    if config.TRADE_START_HOUR <= config.TRADE_END_HOUR:
        return config.TRADE_START_HOUR <= current_hour < config.TRADE_END_HOUR
    else:
        return current_hour >= config.TRADE_START_HOUR or current_hour < config.TRADE_END_HOUR


# ──────────────────────────────────────────────
#  ACTIVE STRATEGIES LIST
# ──────────────────────────────────────────────
def get_active_strategies() -> list:
    strategies = []
    if config.STRATEGY_EMA_PULLBACK: strategies.append("EMA Pullback")
    if config.STRATEGY_MACD: strategies.append("MACD")
    if config.STRATEGY_BOLLINGER: strategies.append("Bollinger")
    if config.STRATEGY_EMA_CROSS: strategies.append("EMA Cross")
    if config.STRATEGY_RSI_REVERSAL: strategies.append("RSI Reversal")
    return strategies


# ──────────────────────────────────────────────
#  MAIN BOT LOOP
# ──────────────────────────────────────────────
def run_bot():
    # 1. Initialize State Persistence
    state_mgr = StateManager()

    # 2. Daily Summary Tracker
    last_summary_date = ""

    strategies = get_active_strategies()

    print("\n" + "="*55)
    print("  🤖 MULTI-STRATEGY TRADING BOT v3.0")
    print("="*55)
    print(f"  Symbols:      {', '.join(config.SYMBOLS.keys())}")
    print(f"  Strategies:   {', '.join(strategies)}")
    print(f"  Min Score:    {config.MIN_SIGNAL_SCORE}%")
    print(f"  Interval:     {config.CHECK_INTERVAL}s")
    print(f"  24/7 Scan:    {'YES' if config.TRADE_START_HOUR==0 else 'NO'}")
    print("="*55 + "\n")

    startup_msg = (
        f"🚀 <b>Trading Bot v3.0 Started!</b>\n\n"
        f"📊 <b>Active Strategies:</b>\n"
    )
    for s in strategies:
        startup_msg += f"  • {s}\n"
    startup_msg += (
        f"\n📍 Watching: <code>{', '.join(config.SYMBOLS.keys())}</code>\n"
        f"🎯 Min Confidence: <code>{config.MIN_SIGNAL_SCORE}%</code>\n"
        f"\nCommands: /start, /status, /chart, /analyze, /help"
    )

    broadcast_message(startup_msg, state_mgr)
    logger.info(f"Bot v3.0 started with strategies: {', '.join(strategies)}")

    while True:
        try:
            # ── Step 1: Manage Commands (Non-blocking) ──
            handle_commands(state_mgr, get_daily_summary, get_market_analysis_data, fetch_data)

            now = datetime.now(timezone.utc)

            # ── Step 2: Hourly Expiry Check & Cleanup ──
            state_mgr.clean_expired_signals()

            # ── Step 3: Scan Cycle (if in hours) ──
            if is_trading_hours():
                for display_name, ticker in config.SYMBOLS.items():
                    # Check for commands during symbol loop for responsiveness
                    handle_commands(state_mgr, get_daily_summary, get_market_analysis_data, fetch_data)

                    if config.DEBUG_MODE:
                        print(f"  🔍 Scanning {display_name}...")

                    data = fetch_data(ticker, display_name)
                    if data is None: continue

                    # Multi-strategy signal check
                    signal = check_signal(data, display_name, state_mgr)

                    if signal:
                        print(f"  🎯 SIGNAL: {signal['type']} {display_name} via {signal['strategy']}")
                        if broadcast_signal(signal, state_mgr):
                            state_mgr.add_active_signal(display_name, signal)
                            logger.info(f"Signal broadcasted: {signal['type']} {display_name} ({signal['strategy']})")
                        else:
                            print("  ❌ No subscribers to receive the signal")

                    time.sleep(2)  # Pause between symbols

            # ── Step 4: Daily Summary Check ──
            if config.SEND_DAILY_SUMMARY:
                today = now.strftime("%Y-%m-%d")
                if now.hour == config.DAILY_SUMMARY_HOUR and today != last_summary_date:
                    summary = get_daily_summary()
                    send_daily_summary(summary, state_mgr)
                    last_summary_date = today
                    logger.info("Daily summary broadcasted")

            # ── Step 5: Sleep ──
            time.sleep(config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n  🛑 Stopping bot...")
            broadcast_message("🛑 Trading Bot Stopped", state_mgr)
            break
        except Exception as e:
            logger.error(f"Main Loop Error: {e}", exc_info=True)
            time.sleep(config.CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()
