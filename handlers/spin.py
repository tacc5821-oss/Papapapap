import logging
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, add_user_history
from config import OWNER_ID, DAILY_SPIN_LIMIT, SPIN_REWARDS, LOG_GROUP_ID
from utils.logger import log_to_group

logger = logging.getLogger(__name__)

async def spin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle spin button callback."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    # Check if user can spin
    today = date.today().isoformat()
    spins_today = user_data.get("spins_today", 0) if user_data.get("last_spin_date") == today else 0
    bonus_spins = user_data.get("spins_left", 0)
    
    # Owner has unlimited spins
    if user.id == OWNER_ID:
        can_spin = True
        spin_type = "owner"
    elif bonus_spins > 0:
        can_spin = True
        spin_type = "bonus"
    elif spins_today < DAILY_SPIN_LIMIT:
        can_spin = True
        spin_type = "daily"
    else:
        can_spin = False
        spin_type = "none"
    
    if not can_spin:
        await query.edit_message_text(
            f"🚫 You have used all your spins for today!\n\n"
            f"🎁 Daily Spins Used: {spins_today}/{DAILY_SPIN_LIMIT}\n"
            f"🎰 Bonus Spins: {bonus_spins}\n"
            f"⏰ Come back tomorrow for more spins!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Perform spin
    reward = calculate_spin_reward()
    
    # Update user data based on spin type
    new_points = user_data["points"] + reward
    
    update_data = {"points": new_points}
    
    if spin_type == "bonus":
        # Use bonus spin
        update_data["spins_left"] = bonus_spins - 1
        remaining_bonus = bonus_spins - 1
    elif spin_type == "daily":
        # Use daily spin
        update_data["spins_today"] = spins_today + 1
        update_data["last_spin_date"] = today
        remaining_bonus = bonus_spins
    else:  # owner
        remaining_bonus = bonus_spins
    
    update_user_data(user.id, update_data)
    
    # Add to history
    spin_source = "Bonus Spin" if spin_type == "bonus" else "Daily Spin" if spin_type == "daily" else "Owner Spin"
    add_user_history(user.id, "Spin", f"Won {reward} points ({spin_source})")
    
    # Show result with proper spin counts
    current_daily = spins_today + (1 if spin_type == "daily" else 0)
    
    result_text = (
        f"🎰 Spin Result!\n\n"
        f"🏆 You won: {reward} points!\n"
        f"💰 Total Points: {new_points}\n"
        f"🎁 Daily Spins: {current_daily}/{DAILY_SPIN_LIMIT if user.id != OWNER_ID else '∞'}\n"
        f"🎰 Bonus Spins: {remaining_bonus}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎁 Spin Again", callback_data="spin")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # Log to group
    await log_spin_result(context, user, reward, new_points)

def calculate_spin_reward():
    """Calculate spin reward based on probability."""
    # Generate random number for probability
    rand = random.random()
    cumulative_prob = 0
    
    for min_points, max_points, probability in SPIN_REWARDS:
        cumulative_prob += probability
        if rand <= cumulative_prob:
            return random.randint(min_points, max_points)
    
    # Fallback to first reward if something goes wrong
    min_points, max_points, _ = SPIN_REWARDS[0]
    return random.randint(min_points, max_points)

async def log_spin_result(context, user, reward, total_points):
    """Log spin result to the log group."""
    username = f"@{user.username}" if user.username else user.first_name
    
    log_message = (
        f"🎰 Spin Result\n"
        f"👤 {username} (ID: {user.id})\n"
        f"🏆 Reward: {reward} Points\n"
        f"💰 Total: {total_points} Points"
    )
    
    await log_to_group(context, log_message)
