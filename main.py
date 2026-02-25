"""
============================================================
  MAIN.PY — Trading Signal Bot v2.0 (Advanced)
============================================================
  Upgraded with:
   - Persistence (Bot state survives restart)
   - Interactive Telegram Commands (/status, /summary, /help)
   - Advanced Signal Logic (Filter, Cooldown, Expiry)
   - Multi-Symbol Scan
============================================================
"""

import time
import logging
from datetime import datetime, timezone

import yfinance as yf
import pandas as pd

import config
from signals import check_signal, get_daily_summary
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
#  MAIN BOT LOOP
# ──────────────────────────────────────────────
def run_bot():
    # 1. Initialize State Persistence
    state_mgr = StateManager()
    
    # 2. Daily Summary Tracker
    last_summary_date = ""

    print("\n" + "="*50)
    print("  🤖 TRADING BOT v2.0 — ADVANCED EDITION")
    print("="*50)
    print(f"  Symbols:   {', '.join(config.SYMBOLS.keys())}")
    print(f"  Interval:  {config.CHECK_INTERVAL}s")
    print(f"  24/7 Scan: {'YES' if config.TRADE_START_HOUR==0 else 'NO'}")
    print("="*50 + "\n")

    broadcast_message(f"🚀 <b>Trading Bot v2.0 Started!</b>\n\nWatching: <code>{', '.join(config.SYMBOLS.keys())}</code>\nCommands: /start, /status, /summary, /help", state_mgr)
    logger.info("Bot started version 2.0 with multi-user support")

    while True:
        try:
            # ── Step 1: Manage Commands (Non-blocking) ──
            handle_commands(state_mgr, get_daily_summary)

            now = datetime.now(timezone.utc)
            
            # ── Step 2: Hourly Expiry Check & Cleanup ──
            state_mgr.clean_expired_signals()

            # ── Step 3: Scan Cycle (if in hours) ──
            if is_trading_hours():
                for display_name, ticker in config.SYMBOLS.items():
                    # Check for updates again during symbol loop for responsiveness
                    handle_commands(state_mgr, get_daily_summary)

                    if config.DEBUG_MODE:
                        print(f"  🔍 Scanning {display_name}...")

                    data = fetch_data(ticker, display_name)
                    if data is None: continue

                    # Check for signal
                    # Note: check_signal handles cooldown, daily limit, and new candle detection
                    signal = check_signal(data, display_name, state_mgr)

                    if signal:
                        print(f"  🎯 SIGNAL: {signal['type']} {display_name}")
                        if broadcast_signal(signal, state_mgr):
                            state_mgr.add_active_signal(display_name, signal)
                            logger.info(f"Signal broadcasted: {signal['type']} {display_name}")
                        else:
                            print("  ❌ No subscribers to receive the signal")

                    time.sleep(2)  # Pause between symbols

            # ── Step 4: Daily Summary Check ──
            if config.SEND_DAILY_SUMMARY:
                today = now.strftime("%Y-%m-%d")
                if now.hour == config.DAILY_SUMMARY_HOUR and today != last_summary_date:
                    summary = get_daily_summary()
                    broadcast_message(f"<b>📋 DAILY SUMMARY ({summary['date']})</b>\n(Use /summary for details)", state_mgr)
                    last_summary_date = today
                    logger.info("Daily summary notice broadcasted")

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
