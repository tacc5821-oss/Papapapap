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
    
    # Daily reset logic (Game logic အသစ်အတွက် လိုအပ်ပါက ဆက်သုံးနိုင်ရန်)
    reset_daily_spins()
    
    # Handle referral
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            user_data = get_user_data(user.id)
            if not user_data.get('referred_by'):
                await handle_referral(user.id, referrer_id, context)
        except (ValueError, IndexError):
            pass
    
    # Get user data
    user_data = get_user_data(user.id)
    update_user_data(user.id, {"username": user.username or ""})
    
    welcome_text = (
        f"🎉 Welcome {user.first_name}!\n\n"
        f"💰 Your MMK: {user_data.get('mmk', 0)} MMK\n"
        f"👥 Total Referrals: {user_data.get('referral_count', 0)}\n\n"
        f"🎯 Choose an option from the menu below:"
    )
    
    keyboard = get_main_menu_keyboard(user.id)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_main_menu_keyboard(user_id):
    """ပင်မ Menu ခလုတ်များ (Spin ကို Crash ဖြင့်၊ Event ကို JP Control ဖြင့် အစားထိုးထားသည်)"""
    keyboard = [
        [InlineKeyboardButton("🚀 ဂိမ်းဆော့ရန်", callback_data="crash_game")],
        [InlineKeyboardButton("💸 Exchange MMK", callback_data="exchange")],
        [InlineKeyboardButton("📨 Invite Friends", callback_data="invite_friends")],
        [InlineKeyboardButton("💰 My MMK", callback_data="my_points")],
        [InlineKeyboardButton("📜 History", callback_data="history")],
        [InlineKeyboardButton("❓ အကူအညီရယူရန်", callback_data="get_help")]
    ]
    
    # Add Admin JP Control for owner (Event နေရာတွင် အစားထိုးခြင်း)
    if user_id == OWNER_ID:
        keyboard.insert(2, [InlineKeyboardButton("🎰 Owner JP Control", callback_data="jackpot_control")])
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
        welcome_text = (
            f"🎉 Welcome {user.first_name}!\n\n"
            f"💰 Your MMK: {user_data.get('mmk', 0)} MMK\n"
            f"👥 Total Referrals: {user_data.get('referral_count', 0)}\n\n"
            f"🎯 Choose an option from the menu below:"
        )
        keyboard = get_main_menu_keyboard(user.id)
        await query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_referral(user_id, referrer_id, context):
    """Referral Logic"""
    if user_id == referrer_id: return
    user_data = get_user_data(user_id)
    referrer_data = get_user_data(referrer_id)
    
    if not user_data.get('referred_by') and referrer_data:
        update_user_data(user_id, {"referred_by": referrer_id})
        current_mmk = referrer_data.get('mmk', 0)
        ref_count = referrer_data.get('referral_count', 0)
        
        # သူငယ်ချင်းဖိတ်လျှင် ဆုကြေးပေးရန် (ဥပမာ 100 MMK)
        update_user_data(referrer_id, {
            "mmk": current_mmk + 100,
            "referral_count": ref_count + 1
        })
        
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text=f"🎉 New referral joined! You received +100 MMK bonus."
            )
        except: pass

async def show_invite_friends(query, user_id):
    """Invite Friends Interface"""
    user_data = get_user_data(user_id)
    referral_count = user_data.get('referral_count', 0)
    
    invite_text = (
        f"📨 Invite Friends → Get Bonus\n\n"
        f"👥 Your referrals: {referral_count}\n"
        f"🎁 Reward: +100 MMK per friend\n\n"
        f"📎 Your referral link:\n"
        f"https://t.me/giftwaychinese_bot?start={user_id}\n\n"
        f"📢 Share this link to earn more!"
    )
    await query.edit_message_text(invite_text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
    ]]))

async def show_help_options(query):
    """Support group link"""
    help_text = (
        f"❓ အကူအညီရယူရန်\n\n"
        f"💬 Join our support group to ask questions and get help!"
    )
    await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Join Support Group", url="https://t.me/+QJb5Z2tH9ME3NDg9")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]))

async def show_my_points(query, user_data):
    """Show user points and stats"""
    points_text = (
        f"📊 Your Statistics\n\n"
        f"💰 Total MMK: {user_data.get('mmk', 0)} MMK\n"
        f"👥 Total Referrals: {user_data.get('referral_count', 0)}\n"
        f"🎯 Event Status: {'✅ Active' if user_data.get('event_done') else '❌ Normal'}"
    )
    await query.edit_message_text(points_text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
    ]]))

async def show_history(query, user_data):
    """Show action history"""
    history = user_data.get("history", [])
    if not history:
        history_text = "📜 No history found."
    else:
        history_text = "📜 Your Recent Activity\n\n"
        for entry in history[-10:]:
            date_str = entry.get("timestamp", "").split("T")[0]
            history_text += f"📅 {date_str}\n{entry.get('action','')}: {entry.get('details','')}\n\n"
    
    await query.edit_message_text(history_text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
    ]]))
