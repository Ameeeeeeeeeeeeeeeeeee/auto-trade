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
def handle_commands(state_mgr, summary_func):
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
            if chat_id != config.TELEGRAM_CHAT_ID: continue

            text = update["message"]["text"].lower()
            
            if text == "/start":
                if state_mgr.subscribe_user(chat_id):
                    send_api_message("<b>✅ Subscribed!</b>\nYou will now receive all trading signals. Send /status to see the current bot state.", chat_id)
                else:
                    send_api_message("<b>👋 You are already subscribed!</b>", chat_id)
            elif text == "/stop":
                if state_mgr.unsubscribe_user(chat_id):
                    send_api_message("<b>🚫 Unsubscribed.</b>\nYou will no longer receive signals. Send /start to resubscribe.", chat_id)
                else:
                    send_api_message("<b>⚠️ You weren't subscribed anyway.</b>", chat_id)
            elif text == "/status":
                send_status(state_mgr, chat_id)
            elif text == "/summary":
                summary = summary_func()
                send_daily_summary(summary, chat_id)
            elif text == "/help":
                send_message("<b>🤖 Available Commands:</b>\n\n/start - Subscribe to signals\n/stop - Unsubscribe from signals\n/status - Current bot status & active signals\n/summary - Today's signal summary\n/help - Show this message", chat_id)
            
    except Exception as e:
        if config.DEBUG_MODE: print(f"  ⚠️ Command Check Error: {e}")


def send_status(state_mgr, chat_id=None):
    active = state_mgr.get_active_signals()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    msg = f"<b>🤖 Bot Status ({today})</b>\n\n"
    msg += f"✅ Monitoring {len(config.SYMBOLS)} symbols\n"
    msg += f"🕒 Timeframe: {config.TIMEFRAME}\n"
    msg += f"🔥 Active Signals: {len(active)}\n\n"
    
    if active:
        msg += "<b>📋 Active List:</b>\n"
        for s, data in active.items():
            msg += f"• {s}: {data['type']} @ {data['entry']}\n"
    
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
