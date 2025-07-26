import json
import os
import logging
from datetime import datetime, date
from config import USER_DATA_FILE, BOT_STATE_FILE

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database files if they don't exist."""
    if not os.path.exists(USER_DATA_FILE):
        save_user_data({})
        logger.info("Created new user data file")
    
    if not os.path.exists(BOT_STATE_FILE):
        save_bot_state({
            "current_event": None,
            "event_participants": [],
            "pending_exchanges": {}
        })
        logger.info("Created new bot state file")

def load_user_data():
    """Load user data from JSON file."""
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    """Save user data to JSON file."""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

def load_bot_state():
    """Load bot state from JSON file."""
    try:
        with open(BOT_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "current_event": None,
            "event_participants": [],
            "pending_exchanges": {}
        }

def save_bot_state(data):
    """Save bot state to JSON file."""
    try:
        with open(BOT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving bot state: {e}")

def get_user_data(user_id):
    """Get user data by ID."""
    data = load_user_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        data[user_id_str] = {
            "user_id": user_id,
            "username": "",
            "points": 0,
            "spins_today": 0,
            "last_spin_date": "",
            "event_done": False,
            "history": []
        }
        save_user_data(data)
    
    return data[user_id_str]

def update_user_data(user_id, updates):
    """Update user data."""
    data = load_user_data()
    user_id_str = str(user_id)
    
    if user_id_str in data:
        data[user_id_str].update(updates)
        save_user_data(data)
        return data[user_id_str]
    return None

def reset_daily_spins():
    """Reset daily spins for all users if date changed."""
    data = load_user_data()
    today = date.today().isoformat()
    
    for user_id, user_data in data.items():
        if user_data.get("last_spin_date") != today:
            user_data["spins_today"] = 0
            user_data["last_spin_date"] = today
    
    save_user_data(data)

def add_user_history(user_id, action, details):
    """Add action to user history."""
    user_data = get_user_data(user_id)
    if "history" not in user_data:
        user_data["history"] = []
    
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    
    user_data["history"].append(history_entry)
    
    # Keep only last 50 entries
    if len(user_data["history"]) > 50:
        user_data["history"] = user_data["history"][-50:]
    
    update_user_data(user_id, {"history": user_data["history"]})
