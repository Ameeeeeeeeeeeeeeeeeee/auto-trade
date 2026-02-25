# 🤖 Telegram Trading Signal Bot

A beginner-friendly Python bot that detects **EMA Pullback + Engulfing** setups and sends trade signals to Telegram.

## 📊 Strategy

| Condition       | Rule                                                                           |
| --------------- | ------------------------------------------------------------------------------ |
| **Trend**       | EMA 20 > EMA 50 = Uptrend (BUY only) / EMA 20 < EMA 50 = Downtrend (SELL only) |
| **Pullback**    | Price touches the zone between EMA 20 and EMA 50                               |
| **Entry**       | Bullish Engulfing (BUY) or Bearish Engulfing (SELL) candle confirmed           |
| **Stop Loss**   | Recent swing high/low (Mode 0) or ATR-based (Mode 1)                           |
| **Take Profit** | Based on Risk:Reward ratio (default 1:2)                                       |

---

## 🚀 Quick Start

### 1. Install Python

Make sure you have **Python 3.10+** installed. Download from [python.org](https://www.python.org/downloads/)

### 2. Install Dependencies

Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

### 3. Set Up Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
4. Open `config.py` and paste it:
   ```python
   TELEGRAM_BOT_TOKEN = "your-token-here"
   ```

### 4. Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Send `/start` — it replies with your Chat ID
3. Paste it in `config.py`:
   ```python
   TELEGRAM_CHAT_ID = "your-chat-id-here"
   ```

### 5. Run the Bot

```bash
python main.py
```

The bot will start monitoring and print debug info to the console. When a signal is found, it sends a formatted message to your Telegram chat!

---

## ⚙️ Configuration

All settings are in **`config.py`**. Key options:

| Setting            | Default  | Description                      |
| ------------------ | -------- | -------------------------------- |
| `SYMBOL`           | `"GC=F"` | Yahoo Finance ticker (Gold)      |
| `TIMEFRAME`        | `"15m"`  | Candle timeframe                 |
| `FAST_EMA`         | `20`     | Fast EMA period                  |
| `SLOW_EMA`         | `50`     | Slow EMA period                  |
| `SL_MODE`          | `1`      | 0 = Swing, 1 = ATR-based         |
| `ATR_MULTIPLIER`   | `1.5`    | ATR × this for SL distance       |
| `RISK_REWARD`      | `2.0`    | TP = SL distance × this          |
| `USE_FIXED_LOT`    | `True`   | True = fixed, False = risk-based |
| `TRADE_START_HOUR` | `8`      | UTC hour to start checking       |
| `TRADE_END_HOUR`   | `20`     | UTC hour to stop checking        |
| `DEBUG_MODE`       | `True`   | Print extra info to console      |

---

## 📁 Project Structure

```
├── config.py          # All settings (edit this!)
├── indicators.py      # EMA, ATR, engulfing detection
├── signals.py         # Trend, pullback, SL/TP logic
├── telegram_bot.py    # Sends messages to Telegram
├── main.py            # Main loop (run this!)
├── requirements.txt   # Python packages
└── README.md          # This file
```

---

## ⚠️ Disclaimer

This bot provides **signals only** — it does NOT execute real trades. Always do your own analysis. Trading involves risk; past performance does not guarantee future results.
