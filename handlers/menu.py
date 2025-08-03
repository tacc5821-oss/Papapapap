import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, reset_daily_spins
from config import OWNER_ID, DAILY_SPIN_LIMIT, REFERRAL_BONUS_SPINS, HELP_GROUP_ID
from datetime import date
from utils.logger import log_to_group

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with referral support."""
    user = update.effective_user
    
    # Reset daily spins if needed
    reset_daily_spins()
    
    # Handle referral if present (only once per user)
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            user_data = get_user_data(user.id)
            # Only process referral if user hasn't been referred before
            if not user_data.get('referred_by'):
                await handle_referral(user.id, referrer_id, context)
        except (ValueError, IndexError):
            pass
    
    # Get or create user data
    user_data = get_user_data(user.id)
    update_user_data(user.id, {"username": user.username or ""})
    
    # Calculate spin information
    today = date.today().isoformat()
    spins_today = user_data.get("spins_today", 0) if user_data.get("last_spin_date") == today else 0
    bonus_spins = user_data.get("spins_left", 0)
    
    welcome_text = (
        f"🎉 Welcome {user.first_name}!\n\n"
        f"💰 Your MMK: {user_data.get('mmk', 0)} MMK\n"
        f"🎁 Daily Spins: {spins_today}/{DAILY_SPIN_LIMIT if user.id != OWNER_ID else '∞'}\n"
        f"🎰 Bonus Spins: {bonus_spins}\n\n"
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
        [InlineKeyboardButton("💸 Exchange MMK", callback_data="exchange")],
        [InlineKeyboardButton("📋 Event", callback_data="event")],
        [InlineKeyboardButton("📨 Invite Friends", callback_data="invite_friends")],
        [InlineKeyboardButton("💰 My MMK", callback_data="my_points")],
        [InlineKeyboardButton("📜 History", callback_data="history")],
        [InlineKeyboardButton("❓ အကူအညီရယူရန်", callback_data="get_help")]
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
    elif query.data == "invite_friends":
        await show_invite_friends(query, user.id)
    elif query.data == "get_help":
        await show_help_options(query)
    elif query.data == "main_menu":
        # Return to main menu
        # Calculate spin information
        today = date.today().isoformat()
        spins_today = user_data.get("spins_today", 0) if user_data.get("last_spin_date") == today else 0
        bonus_spins = user_data.get("spins_left", 0)
        
        welcome_text = (
            f"🎉 Welcome {user.first_name}!\n\n"
            f"💰 Your MMK: {user_data.get('mmk', 0)} MMK\n"
            f"🎁 Daily Spins: {spins_today}/{DAILY_SPIN_LIMIT if user.id != OWNER_ID else '∞'}\n"
            f"🎰 Bonus Spins: {bonus_spins}\n\n"
            f"🎯 Choose an option from the menu below:"
        )
        
        keyboard = get_main_menu_keyboard(user.id)
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_referral(user_id, referrer_id, context):
    """Handle referral when a new user joins via referral link."""
    if user_id == referrer_id:  # Can't refer yourself
        return
    
    user_data = get_user_data(user_id)
    referrer_data = get_user_data(referrer_id)
    
    # Check if user was already referred
    if user_data.get('referred_by'):
        return  # User already used a referral link
    
    # Check if referrer exists
    if not referrer_data:
        return
    
    # Mark user as referred
    update_user_data(user_id, {"referred_by": referrer_id})
    
    # Add bonus spins to referrer
    current_spins = referrer_data.get('spins_left', 0)
    referral_count = referrer_data.get('referral_count', 0)
    
    update_user_data(referrer_id, {
        "spins_left": current_spins + REFERRAL_BONUS_SPINS,
        "referral_count": referral_count + 1
    })
    
    # Get user info
    try:
        user_info = await context.bot.get_chat(user_id)
        username = f"@{user_info.username}" if user_info.username else user_info.first_name
    except Exception:
        username = "New User"
    
    # Notify referrer
    try:
        await context.bot.send_message(
            chat_id=referrer_id,
            text=f"🎉 {username} joined via your link! You got +{REFERRAL_BONUS_SPINS} spins.\n\n"
                 f"🎰 Total bonus spins: {current_spins + REFERRAL_BONUS_SPINS}\n"
                 f"👥 Total referrals: {referral_count + 1}"
        )
    except Exception as e:
        logger.error(f"Failed to notify referrer: {e}")

async def show_invite_friends(query, user_id):
    """Show invite friends interface."""
    user_data = get_user_data(user_id)
    referral_count = user_data.get('referral_count', 0)
    
    invite_text = (
        f"📨 Invite Friends → Get Spins\n\n"
        f"👥 Your referrals: {referral_count}\n"
        f"🎁 Each referral = +{REFERRAL_BONUS_SPINS} spins\n\n"
        f"📎 Your referral link:\n"
        f"https://t.me/giftwaychinese_bot?start={user_id}\n\n"
        f"📢 Share this link with friends!\n"
        f"When they start the bot, you'll get bonus spins."
    )
    
    await query.edit_message_text(
        invite_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
        ]])
    )

async def show_help_options(query):
    """Show help options with group link."""
    help_text = (
        f"❓ အကူအညီရယူရန်\n\n"
        f"📞 Questions? Need help?\n"
        f"💬 Join our support group to ask questions and get help!\n\n"
        f"🔗 Click the button below to join our support group:"
    )
    
    await query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Join Support Group", url=f"https://t.me/joinchat/{abs(HELP_GROUP_ID)}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ])
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
        f"💰 Total MMK: {user_data.get('mmk', 0)} MMK\n"
        f"🎁 Spins Used Today: {spins_used}/{DAILY_SPIN_LIMIT}\n"
        f"🎰 Bonus Spins: {user_data.get('spins_left', 0)}\n"
        f"👥 Referrals: {user_data.get('referral_count', 0)}\n"
        f"🎯 Total Spins: {user_data.get('total_spins_used', 0)}\n"
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
