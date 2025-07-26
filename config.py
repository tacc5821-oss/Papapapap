import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7995053218:AAHjjk02qRGrVmrGy-i-xL4vXio7m8bwaE0")
OWNER_ID = int(os.getenv("OWNER_ID", "1735522859"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1002878767296"))

# Spin system configuration
DAILY_SPIN_LIMIT = 5
SPIN_REWARDS = [
    (10, 30, 0.9),   # min_points, max_points, probability
    (30, 50, 0.5),
    (50, 80, 0.3),
    (80, 100, 0.1),
]

# Exchange configuration
EXCHANGE_AMOUNTS = [500, 1000]
EVENT_REWARD_POINTS = 200

# File paths
USER_DATA_FILE = "user_data.json"
BOT_STATE_FILE = "bot_state.json"
