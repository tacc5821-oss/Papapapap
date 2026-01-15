import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7995053218:AAHjjk02qRGrVmrGy-i-xL4vXio7m8bwaE0")
OWNER_ID = int(os.getenv("OWNER_ID", "1735522859"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1002878767296"))
HELP_GROUP_ID = LOG_GROUP_ID # Support အတွက် Group ID

# --- Crash Game Configuration (စနစ်သစ်) ---
MIN_BET_AMOUNT = 500       # အနည်းဆုံးလောင်းကြေး
MAX_BET_AMOUNT = 100000    # အများဆုံးလောင်းကြေး
OWNER_PROFIT_PERCENT = 0.10 # Owner အတွက် နုတ်ယူမည့် ၁၀% အမြတ်

# --- Multiplier Step (Emoji နှင့် တက်နှုန်းများ) ---
CRASH_MULTIPLIERS = [
    (1.0, "🥚"), (1.1, "🐣"), (1.3, "🐥"), (1.6, "🦅"), 
    (2.0, "✈️"), (2.5, "🚀"), (3.2, "🛸"), (4.0, "☄️")
]

# --- Exchange Configuration (Manual စနစ်) ---
# FIXED AMOUNTS ကို ဖြုတ်လိုက်ပါပြီ (User ကိုယ်တိုင်ရိုက်ရမည်)
MIN_WITHDRAW_AMOUNT = 500   # အနည်းဆုံး ငွေထုတ်ယူနိုင်သော ပမာဏ

# --- Referral System ---
REFERRAL_BONUS_MMK = 100    # သူငယ်ချင်းဖိတ်လျှင် Spin အစား MMK ဆုပေးရန်

# --- Jackpot Configuration (Owner JP Control အတွက်) ---
JACKPOT_WINNERS_COUNT = 5   # Jackpot ပေါက်မည့် လူဦးရေ

# File paths
USER_DATA_FILE = "user_data.json"
BOT_STATE_FILE = "bot_state.json"
