"""
============================================================
  TELEGRAM_BOT.PY — Telegram Interaction (v2.0)
============================================================
  Upgraded with:
   - Command support (/status, /summary, /help)
   - Rich signal formatting with strength bars
   - Non-blocking update handling
============================================================
"""

import requests
import config
from datetime import datetime, timezone

# Track the last update ID to avoid processing the same message twice
LAST_UPDATE_ID = 0

# ──────────────────────────────────────────────
#  FORMAT SIGNAL MESSAGE
# ──────────────────────────────────────────────
def format_signal_message(signal: dict) -> str:
    direction = "🟢 BUY SIGNAL" if signal["type"] == "BUY" else "🔴 SELL SIGNAL"
    
    # Progress bar for strength
    progress = "▓" * (signal["strength_score"] // 10) + "░" * (10 - (signal["strength_score"] // 10))
    strength_details = "\n".join(f"  {d}" for d in signal.get("strength_details", []))

    message = (
        f"<b>{direction}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Symbol: <code>{signal['symbol']}</code>\n"
        f"🕒 Timeframe: <code>{config.TIMEFRAME}</code>\n"
        f"💰 Entry: <code>{signal['entry']}</code>\n"
        f"🛑 SL: <code>{signal['stop_loss']}</code>\n"
        f"🎯 TP: <code>{signal['take_profit']}</code>\n"
        f"📦 Lot: <code>{signal['lot_size']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📉 Trend: {signal['trend']}\n"
        f"📊 RSI: {signal['rsi']} | ATR: {signal['atr']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{signal['strength_emoji']} Confidence: {signal['strength_label']}</b>\n"
        f"<code>{progress} {signal['strength_score']}%</code>\n\n"
        f"{strength_details}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 {signal['strategy']}\n"
        f"⚠️ <i>Trade at your own risk!</i>"
    )
    return message


# ──────────────────────────────────────────────
#  COMMANDS HANDLERS
# ──────────────────────────────────────────────
def handle_commands(state_mgr, summary_func, analysis_func, fetch_func):
    """
    Check for new commands from Telegram.
    Non-blocking polling using getUpdates.
    """
    global LAST_UPDATE_ID
    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"offset": LAST_UPDATE_ID + 1, "timeout": 0}

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200: return

        updates = response.json().get("result", [])
        for update in updates:
            LAST_UPDATE_ID = update["update_id"]
            if "message" not in update or "text" not in update["message"]: continue
            
            chat_id = str(update["message"]["chat"]["id"])
            if chat_id != config.TELEGRAM_CHAT_ID and not state_mgr.is_subscribed(chat_id):
                # Auto-subscribe if they send /start, otherwise ignore or prompt
                if update["message"]["text"].lower() != "/start":
                    continue

            text = update["message"]["text"].lower()
            parts = text.split()
            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            if cmd == "/start":
                if state_mgr.subscribe_user(chat_id):
                    send_api_message("<b>✅ Subscribed!</b>\nYou will now receive all trading signals. Send /status to see the current bot state.", chat_id)
                else:
                    send_api_message("<b>👋 You are already subscribed!</b>", chat_id)
            elif cmd == "/stop":
                if state_mgr.unsubscribe_user(chat_id):
                    send_api_message("<b>🚫 Unsubscribed.</b>\nYou will no longer receive signals. Send /start to resubscribe.", chat_id)
                else:
                    send_api_message("<b>⚠️ You weren't subscribed anyway.</b>", chat_id)
            elif cmd == "/status":
                send_status(state_mgr, chat_id)
            elif cmd == "/summary":
                summary = summary_func()
                send_daily_summary(summary, chat_id)
            elif cmd == "/price":
                handle_price_command(args, fetch_func, chat_id)
            elif cmd == "/analyze":
                handle_analyze_command(args, fetch_func, analysis_func, chat_id)
            elif cmd == "/help":
                msg = (
                    "<b>🤖 Available Commands:</b>\n\n"
                    "/start - Subscribe to signals\n"
                    "/stop - Unsubscribe\n"
                    "/price [pair] - Get live prices\n"
                    "/analyze [pair] - Deep technical analysis\n"
                    "/status - Bot health & active signals\n"
                    "/summary - Today's results\n"
                    "/help - Show this list"
                )
                send_message(msg, chat_id)
            
    except Exception as e:
        if config.DEBUG_MODE: print(f"  ⚠️ Command Check Error: {e}")


    send_message(msg, chat_id)


# ──────────────────────────────────────────────
#  PRICE & ANALYSIS HANDLERS (NEW)
# ──────────────────────────────────────────────
def handle_price_command(args, fetch_func, chat_id):
    if args:
        symbol = args[0].upper()
        ticker = config.SYMBOLS.get(symbol)
        if not ticker:
            send_message(f"❌ Unknown symbol: {symbol}. Available: {', '.join(config.SYMBOLS.keys())}", chat_id)
            return
        
        data = fetch_func(ticker, symbol)
        if data is not None and not data.empty:
            price = data["Close"].iloc[-1]
            send_message(f"💰 <b>{symbol} Current Price</b>\nPrice: <code>{price:.5f}</code>", chat_id)
        else:
            send_message("❌ Error fetching data.", chat_id)
    else:
        # Show all prices
        msg = "<b>💰 Live Prices</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        for s, t in config.SYMBOLS.items():
            data = fetch_func(t, s)
            if data is not None and not data.empty:
                msg += f"• {s}: <code>{data['Close'].iloc[-1]:.5f}</code>\n"
        send_message(msg, chat_id)

def handle_analyze_command(args, fetch_func, analysis_func, chat_id):
    if not args:
        send_message("❓ Please specify a pair to analyze. E.g., <code>/analyze XAUUSD</code>", chat_id)
        return
    
    symbol = args[0].upper()
    ticker = config.SYMBOLS.get(symbol)
    if not ticker:
        send_message(f"❌ Unknown symbol: {symbol}. Available: {', '.join(config.SYMBOLS.keys())}", chat_id)
        return
    
    send_message(f"🔍 Analyzing {symbol}... Please wait.", chat_id)
    data = fetch_func(ticker, symbol)
    if data is None or data.empty:
        send_message("❌ Error fetching market data.", chat_id)
        return
    
    analysis = analysis_func(data, symbol)
    if "error" in analysis:
        send_message(f"❌ {analysis['error']}", chat_id)
        return
    
    msg = (
        f"<b>📊 MARKET ANALYSIS: {symbol}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 Price: <code>{analysis['price']}</code>\n"
        f"📈 Trend: <b>{analysis['trend']}</b> ({analysis['trend_strength']})\n"
        f"📏 EMA Sep: <code>{analysis['ema_separation']}%</code>\n"
        f"💠 RSI: <code>{analysis['rsi']}</code> ({analysis['rsi_status']})\n"
        f"📉 ATR: <code>{analysis['atr']}</code>\n"
        f"🌊 Volatility: {analysis['volatility']}\n\n"
        f"🕒 <i>{analysis['timestamp']}</i>"
    )
    send_message(msg, chat_id)


# ──────────────────────────────────────────────
#  SENDING FUNCTIONS (BROADCASTING)
# ──────────────────────────────────────────────
def broadcast_signal(signal: dict, state_mgr) -> bool:
    """Send a signal to all subscribed users."""
    subscribers = state_mgr.get_subscribers()
    if not subscribers:
        return False
    
    msg = format_signal_message(signal)
    success = False
    for chat_id in subscribers:
        if send_api_message(msg, chat_id):
            success = True
    return success

def send_daily_summary(summary: dict, chat_id=None) -> bool:
    msg = f"<b>📋 DAILY SUMMARY ({summary['date']})</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📊 Total Signals: {summary['total_signals']}\n"
    msg += f"🟢 BUY: {summary['buy_signals']}\n"
    msg += f"🔴 SELL: {summary['sell_signals']}\n"
    
    if summary["signals"]:
        msg += "\n<b>Recent Actions:</b>\n"
        for s in summary["signals"][-5:]:
            emoji = "🟢" if s["type"] == "BUY" else "🔴"
            msg += f"{emoji} {s['symbol']} {s['type']} @ {s['entry']}\n"
    
    if chat_id:
        return send_api_message(msg, chat_id)
    else:
        # Broadcast if no specific chat_id
        return broadcast_message(msg, None)  # state_mgr needed for broadcast

def broadcast_message(text: str, state_mgr) -> bool:
    """Send a plain text message to all subscribers."""
    subscribers = state_mgr.get_subscribers()
    if not subscribers:
        return False
    
    success = False
    for chat_id in subscribers:
        if send_api_message(text, chat_id):
            success = True
    return success

def send_message(text: str, chat_id=None) -> bool:
    """Send a message to a specific user (or broadcast if no ID, but needs state_mgr)."""
    if chat_id:
        return send_api_message(text, chat_id)
    return False # Use broadcast_message for broadcasting

def send_api_message(text: str, chat_id=None) -> bool:
    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": return False
    
    # Use config ID if none provided
    target_id = chat_id if chat_id else config.TELEGRAM_CHAT_ID
    if not target_id: return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except: return False
