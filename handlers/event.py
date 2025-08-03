import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, load_bot_state, add_user_history
from config import EVENT_REWARD_MMK
from utils.logger import log_to_group

logger = logging.getLogger(__name__)

async def event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event button callback."""
    query = update.callback_query
    await query.answer()
    
    bot_state = load_bot_state()
    current_event = bot_state.get("current_event")
    
    if not current_event:
        await query.edit_message_text(
            f"📋 No Active Event\n\n"
            f"❌ There is no active event at the moment.\n"
            f"⏳ Please wait for admin to start a new event.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    # Check if user already completed the event
    if user_data.get("event_done", False):
        await query.edit_message_text(
            f"📋 Event Already Completed\n\n"
            f"✅ You have already completed this event!\n"
            f"🎁 Reward: {EVENT_REWARD_POINTS} points\n\n"
            f"⏳ Wait for the next event to earn more points.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Show event details with participant count
    channels = current_event.get("channels", [])
    participant_limit = current_event.get("participant_limit", 30)
    current_participants = len(bot_state.get("event_participants", []))
    
    # Check if event is full
    if current_participants >= participant_limit:
        await query.edit_message_text(
            f"📢 Event Full!\n\n"
            f"👥 Participants: {current_participants}/{participant_limit}\n"
            f"❌ Sorry, this event has reached its participant limit.\n\n"
            f"⏳ Please wait for the next event.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    event_text = f"📢 Active Event!\n\n👥 Participants: {current_participants}/{participant_limit}\n\n📋 Join the following channels and click ✅ Done when finished:\n\n"
    
    keyboard = []
    for i, channel in enumerate(channels):
        channel_name = f"Channel {i+1}"
        keyboard.append([InlineKeyboardButton(f"📎 {channel_name}", url=channel)])
    
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="event_done")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        event_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def event_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event done button callback."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    bot_state = load_bot_state()
    
    # Check if there's an active event
    current_event = bot_state.get("current_event")
    if not current_event:
        await query.edit_message_text(
            f"❌ No active event found!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Check participant limit
    participant_limit = current_event.get("participant_limit", 30)
    current_participants = len(bot_state.get("event_participants", []))
    
    if current_participants >= participant_limit:
        await query.edit_message_text(
            f"📢 Event Full!\n\n"
            f"👥 Participants: {current_participants}/{participant_limit}\n"
            f"❌ Sorry, this event has reached its participant limit.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Check if user already completed the event
    if user_data.get("event_done", False):
        await query.edit_message_text(
            f"✅ You have already completed this event!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Mark event as completed and give reward
    current_mmk = user_data.get("mmk", 0)
    new_mmk = current_mmk + EVENT_REWARD_MMK
    update_user_data(user.id, {
        "mmk": new_mmk,
        "event_done": True
    })
    
    # Add to history
    add_user_history(user.id, "Event", f"Completed event, earned {EVENT_REWARD_MMK} MMK")
    
    # Add to participants list
    if "event_participants" not in bot_state:
        bot_state["event_participants"] = []
    
    participant_info = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "completed_at": str(query.message.date)
    }
    bot_state["event_participants"].append(participant_info)
    
    from database import save_bot_state
    save_bot_state(bot_state)
    
    # Show completion message
    await query.edit_message_text(
        f"🎯 Event Completed!\n\n"
        f"✅ Congratulations! You have successfully completed the event.\n"
        f"🎁 Reward: {EVENT_REWARD_MMK} MMK\n"
        f"💰 Total MMK: {new_mmk} MMK",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
        ]])
    )
    
    # Log to group
    await log_event_completion(context, user, new_mmk)

async def log_event_completion(context, user, total_mmk):
    """Log event completion to the log group."""
    username = f"@{user.username}" if user.username else user.first_name
    
    log_message = (
        f"🎯 Event Completed\n"
        f"👤 {username} (ID: {user.id})\n"
        f"🎁 Rewarded: {EVENT_REWARD_MMK} MMK\n"
        f"💰 Total: {total_mmk} MMK"
    )
    
    await log_to_group(context, log_message)
