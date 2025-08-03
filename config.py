import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7995053218:AAHjjk02qRGrVmrGy-i-xL4vXio7m8bwaE0")
OWNER_ID = int(os.getenv("OWNER_ID", "1735522859"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1002878767296"))

# Spin system configuration
DAILY_SPIN_LIMIT = 5
SPIN_REWARDS = [
    (100, 300, 0.9),   # min_mmk, max_mmk, probability (MMK instead of points)
    (300, 500, 0.5),
    (500, 800, 0.3),
    (800, 1000, 0.1),
]

# Exchange configuration (MMK amounts)
EXCHANGE_AMOUNTS = [5000, 10000, 20000]  # MMK amounts
EVENT_REWARD_MMK = 2000  # MMK instead of points

# Referral system
REFERRAL_BONUS_SPINS = 3
HELP_GROUP_ID = -1002878767296  # Same as LOG_GROUP_ID for help support

# Event configuration
DEFAULT_EVENT_PARTICIPANT_LIMIT = 30
EVENT_PARTICIPANT_LIMITS = [10, 20, 30, 50, 100]  # Available limit options

# File paths
USER_DATA_FILE = "user_data.json"
BOT_STATE_FILE = "bot_state.json"
