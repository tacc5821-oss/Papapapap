import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, reset_daily_spins
from config import OWNER_ID

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    user = update.effective_user
    
    # Reset daily spins if needed
    reset_daily_spins()
    
    # Get or create user data
    user_data = get_user_data(user.id)
    update_user_data(user.id, {"username": user.username or ""})
    
    welcome_text = (
        f"🎉 Welcome {user.first_name}!\n\n"
        f"💰 Your Points: {user_data['points']}\n"
        f"🎯 Choose an option from the menu below:"
    )
    
    keyboard = get_main_menu_keyboard(user.id)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard based on user privileges."""
    keyboard = [
        [InlineKeyboardButton("🎁 Spin", callback_data="spin")],
        [InlineKeyboardButton("📤 Exchange Points", callback_data="exchange")],
        [InlineKeyboardButton("📋 Event", callback_data="event")],
        [InlineKeyboardButton("📊 My Points", callback_data="my_points")],
        [InlineKeyboardButton("📜 History", callback_data="history")]
    ]
    
    # Add admin menu for owner
    if user_id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("🧑‍💼 Admin Panel", callback_data="admin_panel")])
    
    return keyboard

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu callback."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    if query.data == "my_points":
        await show_my_points(query, user_data)
    elif query.data == "history":
        await show_history(query, user_data)
    else:
        # Return to main menu
        welcome_text = (
            f"🎉 Welcome {user.first_name}!\n\n"
            f"💰 Your Points: {user_data['points']}\n"
            f"🎯 Choose an option from the menu below:"
        )
        
        keyboard = get_main_menu_keyboard(user.id)
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def show_my_points(query, user_data):
    """Show user points and spins information."""
    from config import DAILY_SPIN_LIMIT
    from datetime import date
    
    today = date.today().isoformat()
    spins_used = user_data.get("spins_today", 0) if user_data.get("last_spin_date") == today else 0
    spins_remaining = max(0, DAILY_SPIN_LIMIT - spins_used)
    
    points_text = (
        f"📊 Your Statistics\n\n"
        f"💰 Total Points: {user_data['points']}\n"
        f"🎁 Spins Used Today: {spins_used}/{DAILY_SPIN_LIMIT}\n"
        f"🔄 Spins Remaining: {spins_remaining}\n"
        f"🎯 Event Status: {'✅ Completed' if user_data.get('event_done') else '❌ Not Completed'}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        points_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_history(query, user_data):
    """Show user action history."""
    history = user_data.get("history", [])
    
    if not history:
        history_text = "📜 No history found.\n\nStart spinning or exchanging points to see your activity here!"
    else:
        history_text = "📜 Your Recent Activity\n\n"
        
        # Show last 10 entries
        for entry in history[-10:]:
            timestamp = entry.get("timestamp", "").split("T")[0]  # Get date only
            action = entry.get("action", "")
            details = entry.get("details", "")
            history_text += f"📅 {timestamp}\n{action}: {details}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
    
    await query.edit_message_text(
        history_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
