"""
============================================================
  CONFIG.PY — All Configurable Settings for the Trading Bot
============================================================
  Edit the values below to customize the bot behavior.
============================================================
"""

# ──────────────────────────────────────────────
#  TELEGRAM SETTINGS
# ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "8525447911:AAFCw08b0Nw4LWJ1tBkSyCELd1xfYN5R198"

# Optional: Set this to your Chat ID for admin notifications 
# or as a fallback if the subscriber list is empty.
TELEGRAM_CHAT_ID = "7246324907"

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
#  EMA SETTINGS
# ──────────────────────────────────────────────
FAST_EMA = 20
SLOW_EMA = 50

# ── Trend Strength Filter (NEW) ──
# Minimum % distance between EMA 20 and EMA 50 to consider it a "strong" trend.
# Prevents trading in flat/sideways markets.
TREND_STRENGTH_THRESHOLD = 0.01  # Lowered from 0.05% for easier signal detection

# ──────────────────────────────────────────────
#  RSI SETTINGS
# ──────────────────────────────────────────────
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
USE_RSI_FILTER = True

# ── RSI 50-Level Filter (NEW) ──
# BUY only if RSI > 50 | SELL only if RSI < 50
USE_RSI_50_CROSS = True

# ──────────────────────────────────────────────
#  VOLATILITY FILTER (NEW)
# ──────────────────────────────────────────────
# Minimum ATR value to allow a trade (prevents trading in "dead" markets)
USE_VOLATILITY_FILTER = True
MIN_ATR_VALUE = {
    "XAUUSD": 1.0,    # Gold needs higher ATR
    "EURUSD": 0.0001,  # Forex needs much lower
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
SL_MODE = 1
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5
SWING_LOOKBACK = 10
RISK_REWARD = 2.0

# ──────────────────────────────────────────────
#  RISK & EXPIRY (NEW)
# ──────────────────────────────────────────────
USE_FIXED_LOT = True
FIXED_LOT_SIZE = 0.10
RISK_PERCENT = 1.0
ACCOUNT_BALANCE = 10000

# ── Signal Expiry ──
# How long (in hours) a signal stays "active" before being auto-removed.
SIGNAL_EXPIRY_HOURS = 1.0

# ── Signal Cooldown ──
# Minutes to wait before allowing another signal on the same symbol.
SIGNAL_COOLDOWN_MINUTES = 60

# ── Daily Limit ──
# Max signals allowed per symbol per day.
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
