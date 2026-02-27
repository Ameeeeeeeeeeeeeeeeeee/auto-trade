"""
============================================================
  CONFIG.PY — All Configurable Settings (v3.0)
============================================================
  Multi-Strategy Trading Bot Configuration
  Edit the values below to customize the bot behavior.
============================================================
"""

import os

# ──────────────────────────────────────────────
#  TELEGRAM SETTINGS
# ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8525447911:AAFCw08b0Nw4LWJ1tBkSyCELd1xfYN5R198")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7246324907")

# ──────────────────────────────────────────────
#  MULTI-SYMBOL MONITORING
# ──────────────────────────────────────────────
SYMBOLS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "BTCUSD": "BTC-USD",
}

TIMEFRAME = "1h"
DATA_PERIOD = "30d"

# ──────────────────────────────────────────────
#  STRATEGY TOGGLES (NEW v3.0)
# ──────────────────────────────────────────────
# Enable/disable individual strategies
STRATEGY_EMA_PULLBACK = True     # Original: EMA Pullback + Engulfing
STRATEGY_MACD = True             # MACD Crossover signals
STRATEGY_BOLLINGER = True        # Bollinger Band Bounce
STRATEGY_EMA_CROSS = True        # EMA Fast/Slow Crossover
STRATEGY_RSI_REVERSAL = True     # RSI Oversold/Overbought Reversal

# Minimum signal confidence score to send (0-100)
# Higher = fewer but better signals
MIN_SIGNAL_SCORE = 25

# ──────────────────────────────────────────────
#  EMA SETTINGS
# ──────────────────────────────────────────────
FAST_EMA = 20
SLOW_EMA = 50

# Minimum % distance between EMAs to consider a "strong" trend.
TREND_STRENGTH_THRESHOLD = 0.01

# ──────────────────────────────────────────────
#  MACD SETTINGS (NEW)
# ──────────────────────────────────────────────
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ──────────────────────────────────────────────
#  BOLLINGER BAND SETTINGS (NEW)
# ──────────────────────────────────────────────
BB_PERIOD = 20
BB_STD_DEV = 2.0

# ──────────────────────────────────────────────
#  RSI SETTINGS
# ──────────────────────────────────────────────
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
USE_RSI_FILTER = True

# BUY only if RSI > 50 | SELL only if RSI < 50
# (Only applied to EMA Pullback strategy)
USE_RSI_50_CROSS = True

# ──────────────────────────────────────────────
#  VOLATILITY FILTER
# ──────────────────────────────────────────────
USE_VOLATILITY_FILTER = True
MIN_ATR_VALUE = {
    "XAUUSD": 1.0,
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "BTCUSD": 10.0,
}

# ──────────────────────────────────────────────
#  PULLBACK SETTINGS
# ──────────────────────────────────────────────
PULLBACK_BARS = 5

# ──────────────────────────────────────────────
#  STOP LOSS & TAKE PROFIT
# ──────────────────────────────────────────────
SL_MODE = 1          # 0 = Swing High/Low, 1 = ATR-based
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5
SWING_LOOKBACK = 10
RISK_REWARD = 2.0

# ──────────────────────────────────────────────
#  RISK & EXPIRY
# ──────────────────────────────────────────────
USE_FIXED_LOT = True
FIXED_LOT_SIZE = 0.10
RISK_PERCENT = 1.0
ACCOUNT_BALANCE = 10000

# Signal Expiry (hours)
SIGNAL_EXPIRY_HOURS = 1.0

# Cooldown between signals on same symbol (minutes)
SIGNAL_COOLDOWN_MINUTES = 60

# Max signals per symbol per day
MAX_SIGNALS_PER_DAY = 5

# ──────────────────────────────────────────────
#  PERSISTENCE
# ──────────────────────────────────────────────
STATE_FILE_PATH = "bot_state.json"

# ──────────────────────────────────────────────
#  TIME FILTER (24h = 0 to 24)
# ──────────────────────────────────────────────
TRADE_START_HOUR = 0
TRADE_END_HOUR = 24

# ──────────────────────────────────────────────
#  BOT BEHAVIOR
# ──────────────────────────────────────────────
CHECK_INTERVAL = 60
DEBUG_MODE = True
LOG_SIGNALS_TO_CSV = True
SIGNAL_LOG_FILE = "signal_history.csv"
SEND_DAILY_SUMMARY = True
DAILY_SUMMARY_HOUR = 23
