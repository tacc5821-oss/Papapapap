import json
import os
import logging
from datetime import datetime, date
from config import USER_DATA_FILE, BOT_STATE_FILE

logger = logging.getLogger(__name__)

def init_database():
    """Database ဖိုင်များမရှိပါက အသစ်ဆောက်ပေးခြင်း"""
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
    """JSON ဖိုင်မှ User data များကို ဖတ်ယူခြင်း"""
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    """User data များကို JSON ဖိုင်ထဲသို့ သိမ်းဆည်းခြင်း"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

def load_bot_state():
    """Bot ၏ အခြေအနေ (Pending List စသည်) ကို ဖတ်ယူခြင်း"""
    try:
        with open(BOT_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current_event": None, "event_participants": [], "pending_exchanges": {}}

def save_bot_state(data):
    """Bot ၏ အခြေအနေကို သိမ်းဆည်းခြင်း"""
    try:
        with open(BOT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving bot state: {e}")

def get_user_data(user_id):
    """User တစ်ယောက်ချင်းစီ၏ အချက်အလက်ကို ယူခြင်း (မရှိပါက အသစ်ဆောက်ပေးခြင်း)"""
    data = load_user_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        data[user_id_str] = {
            "user_id": user_id,
            "username": "",
            "mmk": 0,
            "total_games_played": 0,
            "history": [],
            "referred_by": None,
            "referral_count": 0,
            "event_done": False,
            "last_active": datetime.now().isoformat()
        }
        save_user_data(data)
    
    return data[user_id_str]

def update_user_data(user_id, updates):
    """User data ကို Update ပြုလုပ်ခြင်း"""
    data = load_user_data()
    user_id_str = str(user_id)
    
    if user_id_str in data:
        data[user_id_str].update(updates)
        save_user_data(data)
        return data[user_id_str]
    return None

def get_all_users():
    """Database ထဲရှိ အသုံးပြုသူအားလုံး၏ စာရင်းကို List အနေဖြင့် ယူခြင်း (Jackpot အတွက်)"""
    data = load_user_data()
    users_list = []
    for user_id_str, user_info in data.items():
        user_info['user_id'] = int(user_id_str)
        users_list.append(user_info)
    return users_list

def add_user_history(user_id, action, details):
    """User ၏ လှုပ်ရှားမှုမှတ်တမ်းကို သိမ်းဆည်းခြင်း"""
    user_data = get_user_data(user_id)
    if "history" not in user_data:
        user_data["history"] = []
    
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details
    }
    user_data["history"].append(history_entry)
    
    # နောက်ဆုံး မှတ်တမ်း ၂၀ ခုသာ ထားရှိခြင်း
    if len(user_data["history"]) > 20:
        user_data["history"] = user_data["history"][-20:]
        
    update_user_data(user_id, {"history": user_data["history"]})

def reset_daily_spins():
    """(Crash Game စနစ်တွင် အသုံးမလိုသော်လည်း error မတက်စေရန် ထားရှိခြင်း)"""
    pass
