"""
============================================================
  STATE_MANAGER.PY — Data Persistence
============================================================
  Handles saving and loading the bot's current state
  to a JSON file so results survive a restart.
============================================================
"""

import json
import os
from datetime import datetime, timezone
import config

class StateManager:
    def __init__(self):
        self.file_path = config.STATE_FILE_PATH
        self.state = {
            "active_signals": {},      # {symbol: {signal_data}}
            "last_signal_time": {},    # {symbol: timestamp_str}
            "daily_counts": {},        # {date_str: {symbol: count}}
            "last_candle_times": {},   # {symbol: timestamp_str}
            "subscribers": [],         # List of subscribed chat IDs
        }
        self.load_state()

    def load_state(self):
        """Load state from JSON file if it exists."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    loaded_state = json.load(f)
                    # Merge loaded state into default state structure
                    self.state.update(loaded_state)
            except Exception as e:
                print(f"  ⚠️ Error loading state file: {e}")

    def save_state(self):
        """Save current state to JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"  ⚠️ Error saving state file: {e}")

    # ── Active Signals ──
    def add_active_signal(self, symbol, signal):
        self.state["active_signals"][symbol] = signal
        self.state["last_signal_time"][symbol] = datetime.now(timezone.utc).isoformat()
        self.increment_daily_count(symbol)
        self.save_state()

    def remove_active_signal(self, symbol):
        if symbol in self.state["active_signals"]:
            del self.state["active_signals"][symbol]
            self.save_state()

    def get_active_signals(self):
        return self.state["active_signals"]

    # ── Subscribers ──
    def subscribe_user(self, chat_id):
        """Add a new chat ID to subscribers if not already present."""
        chat_id = str(chat_id)
        if chat_id not in self.state["subscribers"]:
            self.state["subscribers"].append(chat_id)
            self.save_state()
            return True
        return False

    def is_subscribed(self, chat_id):
        return str(chat_id) in self.state["subscribers"]

    def get_subscribers(self):
        # Fallback to config admin if list is empty
        if not self.state["subscribers"] and config.TELEGRAM_CHAT_ID:
            return [config.TELEGRAM_CHAT_ID]
        return self.state["subscribers"]

    def unsubscribe_user(self, chat_id):
        chat_id = str(chat_id)
        if chat_id in self.state["subscribers"]:
            self.state["subscribers"].remove(chat_id)
            self.save_state()
            return True
        return False

    # ── Daily Counts ──
    def increment_daily_count(self, symbol):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today not in self.state["daily_counts"]:
            self.state["daily_counts"][today] = {}
        
        count = self.state["daily_counts"][today].get(symbol, 0)
        self.state["daily_counts"][today][symbol] = count + 1

    def get_daily_count(self, symbol):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.state["daily_counts"].get(today, {}).get(symbol, 0)

    # ── Cooldown ──
    def is_in_cooldown(self, symbol):
        last_time_str = self.state["last_signal_time"].get(symbol)
        if not last_time_str:
            return False
        
        last_time = datetime.fromisoformat(last_time_str)
        elapsed = (datetime.now(timezone.utc) - last_time).total_seconds() / 60
        return elapsed < config.SIGNAL_COOLDOWN_MINUTES

    # ── New Candle Detection ──
    def is_new_candle(self, symbol, current_timestamp):
        """Check if we have already sent a signal for this specific candle timestamp."""
        last_processed_ts = self.state["last_candle_times"].get(symbol)
        if last_processed_ts == str(current_timestamp):
            return False
        return True

    def mark_candle_processed(self, symbol, timestamp):
        """Mark a candle timestamp as processed so we don't send duplicate signals for it."""
        self.state["last_candle_times"][symbol] = str(timestamp)
        self.save_state()

    # ── Expiry ──
    def clean_expired_signals(self):
        """Remove signals that have been active longer than config.SIGNAL_EXPIRY_HOURS."""
        to_remove = []
        now = datetime.now(timezone.utc)
        
        for symbol, signal_time_str in self.state["last_signal_time"].items():
            if symbol not in self.state["active_signals"]:
                continue
                
            signal_time = datetime.fromisoformat(signal_time_str)
            hours_elapsed = (now - signal_time).total_seconds() / 3600
            
            if hours_elapsed >= config.SIGNAL_EXPIRY_HOURS:
                to_remove.append(symbol)
        
        for symbol in to_remove:
            print(f"  ⏰ Signal for {symbol} expired after {config.SIGNAL_EXPIRY_HOURS}h. Removing from active.")
            del self.state["active_signals"][symbol]
            
        if to_remove:
            self.save_state()
