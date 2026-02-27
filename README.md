# 🤖 Multi-Strategy Trading Signal Bot v3.0

A Telegram-based trading signal bot that monitors multiple currency pairs using **5 trading strategies** running in parallel. Sends professional signals, candlestick charts, and deep market analysis to subscribers.

## � Features

### Trading Strategies

| #   | Strategy                     | Description                                                          |
| --- | ---------------------------- | -------------------------------------------------------------------- |
| 1   | **EMA Pullback + Engulfing** | Price retraces to EMA zone then engulfing candle confirms entry      |
| 2   | **MACD Crossover**           | MACD line crosses signal line, confirmed by trend & RSI              |
| 3   | **Bollinger Band Bounce**    | Price bounces off upper/lower band with RSI confirmation             |
| 4   | **EMA Crossover**            | Fast EMA crosses slow EMA with volume/RSI filter                     |
| 5   | **RSI Reversal**             | RSI exits overbought/oversold zones with candle pattern confirmation |

### Bot Features

- 📊 **Multi-symbol scanning** — XAUUSD, EURUSD, GBPUSD, BTCUSD
- 🧠 **Multi-strategy confluence** — signals scored by how many strategies agree
- 📈 **Candlestick chart generation** — professional dark-themed charts with EMA + RSI
- 📝 **Deep word analysis** — comprehensive written market reports
- 👥 **Multi-user support** — unlimited subscribers via /start
- 💾 **State persistence** — survives restarts
- 📋 **Daily summaries** — auto-sent at configured hour
- ⏰ **Cooldown & limits** — prevents signal spam

## 📱 Telegram Commands

| Command           | Description                         |
| ----------------- | ----------------------------------- |
| `/start`          | Subscribe to signals                |
| `/stop`           | Unsubscribe                         |
| `/price [pair]`   | Get live prices                     |
| `/chart [pair]`   | � Candlestick chart with indicators |
| `/analyze [pair]` | 🧠 Deep word + chart analysis       |
| `/status`         | Bot health & active signals         |
| `/summary`        | Today's signal summary              |
| `/help`           | Show all commands                   |

## 🛠️ Setup

### Local Development

```bash
pip install -r requirements.txt
python main.py
```

### Railway Deployment

1. Push code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repo
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` — Your bot token
   - `TELEGRAM_CHAT_ID` — Your admin chat ID
5. Railway will auto-deploy from `railway.json`

### Environment Variables

| Variable             | Description              | Required |
| -------------------- | ------------------------ | -------- |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API Token   | Yes      |
| `TELEGRAM_CHAT_ID`   | Admin Chat ID (fallback) | Yes      |

## 📂 Project Structure

```
├── main.py            # Bot entry point & main loop
├── config.py          # All configurable settings
├── signals.py         # Multi-strategy signal engine
├── indicators.py      # Technical indicators (EMA, RSI, MACD, BB, etc.)
├── chart_analysis.py  # Chart generation & deep analysis
├── telegram_bot.py    # Telegram API interaction
├── state_manager.py   # Persistence & state management
├── requirements.txt   # Python dependencies
├── railway.json       # Railway deployment config
├── nixpacks.toml      # Railway build config
├── Procfile           # Heroku/Render worker config
└── runtime.txt        # Python version
```

## ⚙️ Configuration

All settings are in `config.py`. Key options:

```python
# Enable/disable strategies
STRATEGY_EMA_PULLBACK = True
STRATEGY_MACD = True
STRATEGY_BOLLINGER = True
STRATEGY_EMA_CROSS = True
STRATEGY_RSI_REVERSAL = True

# Minimum signal confidence (0-100)
MIN_SIGNAL_SCORE = 25
```

## ⚠️ Disclaimer

This bot is for educational purposes only. Trading involves risk. Do not trade with money you cannot afford to lose.
