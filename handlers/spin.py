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
    
    # Owner has unlimited spins
    if user.id != OWNER_ID and spins_today >= DAILY_SPIN_LIMIT:
        await query.edit_message_text(
            f"🚫 You have used all your spins for today!\n\n"
            f"🎁 Spins Used: {spins_today}/{DAILY_SPIN_LIMIT}\n"
            f"⏰ Come back tomorrow for more spins!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Perform spin
    reward = calculate_spin_reward()
    
    # Update user data
    new_points = user_data["points"] + reward
    new_spins = spins_today + 1 if user.id != OWNER_ID else spins_today
    
    update_user_data(user.id, {
        "points": new_points,
        "spins_today": new_spins,
        "last_spin_date": today
    })
    
    # Add to history
    add_user_history(user.id, "Spin", f"Won {reward} points")
    
    # Show result
    result_text = (
        f"🎰 Spin Result!\n\n"
        f"🏆 You won: {reward} points!\n"
        f"💰 Total Points: {new_points}\n"
        f"🎁 Spins Used Today: {new_spins}/{DAILY_SPIN_LIMIT if user.id != OWNER_ID else '∞'}"
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
