import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import load_bot_state, save_bot_state, get_user_data, update_user_data, add_user_history
from config import OWNER_ID
from utils.logger import log_to_group

logger = logging.getLogger(__name__)

# Store admin state
admin_states = {}

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callback."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check if user is owner
    if user.id != OWNER_ID:
        await query.edit_message_text("❌ Access denied. You are not authorized.")
        return
    
    if query.data == "admin_panel":
        await show_admin_panel(query)
    elif query.data == "admin_start_event":
        await start_event_creation(query, context)
    elif query.data == "admin_view_participants":
        await view_event_participants(query)
    elif query.data == "admin_cancel_event":
        await cancel_current_event(query, context)

async def show_admin_panel(query):
    """Show admin panel."""
    bot_state = load_bot_state()
    current_event = bot_state.get("current_event")
    
    admin_text = "🧑‍💼 Admin Panel\n\n"
    
    if current_event:
        admin_text += f"📢 Current Event: Active\n"
        admin_text += f"📊 Participants: {len(bot_state.get('event_participants', []))}\n\n"
    else:
        admin_text += f"📢 Current Event: None\n\n"
    
    keyboard = []
    
    if not current_event:
        keyboard.append([InlineKeyboardButton("📢 Start Event", callback_data="admin_start_event")])
    else:
        keyboard.append([InlineKeyboardButton("📄 View Participants", callback_data="admin_view_participants")])
        keyboard.append([InlineKeyboardButton("❌ Cancel Event", callback_data="admin_cancel_event")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        admin_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_event_creation(query, context):
    """Start event creation process."""
    admin_states[query.from_user.id] = "waiting_for_channels"
    
    await query.edit_message_text(
        f"📢 Create New Event\n\n"
        f"Please send up to 10 Telegram channel links.\n"
        f"Send them one by one or all at once.\n\n"
        f"Example:\n"
        f"https://t.me/channel1\n"
        f"https://t.me/channel2\n\n"
        f"Type /cancel to cancel event creation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_panel")
        ]])
    )

async def handle_event_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel links from admin."""
    user = update.effective_user
    
    if user.id != OWNER_ID or admin_states.get(user.id) != "waiting_for_channels":
        return
    
    text = update.message.text
    
    if text == "/cancel":
        admin_states.pop(user.id, None)
        await update.message.reply_text("❌ Event creation cancelled.")
        return
    
    # Extract Telegram channel links
    channel_pattern = r'https://t\.me/[a-zA-Z0-9_]+'
    channels = re.findall(channel_pattern, text)
    
    if not channels:
        await update.message.reply_text(
            "❌ No valid Telegram channel links found.\n"
            "Please send links in format: https://t.me/channelname"
        )
        return
    
    if len(channels) > 10:
        channels = channels[:10]
        await update.message.reply_text(
            f"⚠️ Too many channels! Using first 10 channels only."
        )
    
    # Show preview
    preview_text = "📋 Event Preview\n\n📋 Join the following channels and click ✅ Done when finished:\n\n"
    
    keyboard = []
    for i, channel in enumerate(channels):
        channel_name = f"Channel {i+1}"
        keyboard.append([InlineKeyboardButton(f"📎 {channel_name}", url=channel)])
    
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="event_done")])
    
    preview_text += "\n🕑 Status: Waiting for event confirmation."
    
    keyboard.append([
        InlineKeyboardButton("✅ Confirm Event", callback_data=f"event_confirm_{len(channels)}"),
        InlineKeyboardButton("❌ Cancel Event", callback_data="event_cancel_creation")
    ])
    
    # Store channels temporarily
    context.user_data['pending_channels'] = channels
    admin_states[user.id] = "confirming_event"
    
    await update.message.reply_text(
        preview_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def event_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        return
    
    channels = context.user_data.get('pending_channels', [])
    
    if not channels:
        await query.edit_message_text("❌ No channels found. Please try again.")
        return
    
    # Create event
    bot_state = load_bot_state()
    bot_state["current_event"] = {
        "channels": channels,
        "created_at": str(query.message.date)
    }
    bot_state["event_participants"] = []
    save_bot_state(bot_state)
    
    # Reset all users' event status
    from database import load_user_data, save_user_data
    user_data = load_user_data()
    for user_id in user_data:
        user_data[user_id]["event_done"] = False
    save_user_data(user_data)
    
    # Clear admin state
    admin_states.pop(query.from_user.id, None)
    context.user_data.pop('pending_channels', None)
    
    await query.edit_message_text(
        f"✅ Event Created Successfully!\n\n"
        f"📊 Channels: {len(channels)}\n"
        f"📢 Event is now active for all users.\n"
        f"🎁 Reward: 200 points per completion",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
        ]])
    )
    
    # Notify all users about new event (this would require broadcasting logic)
    logger.info(f"New event created with {len(channels)} channels")

async def event_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event cancellation."""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        return
    
    if query.data == "event_cancel_creation":
        # Cancel event creation
        admin_states.pop(query.from_user.id, None)
        context.user_data.pop('pending_channels', None)
        
        await query.edit_message_text(
            "❌ Event creation cancelled.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
            ]])
        )
    else:
        # Cancel current event
        await cancel_current_event(query, None)

async def cancel_current_event(query, context):
    """Cancel current active event."""
    bot_state = load_bot_state()
    
    if not bot_state.get("current_event"):
        await query.edit_message_text(
            "❌ No active event to cancel.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
            ]])
        )
        return
    
    # Clear event
    bot_state["current_event"] = None
    bot_state["event_participants"] = []
    save_bot_state(bot_state)
    
    await query.edit_message_text(
        "❌ Event cancelled successfully.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
        ]])
    )

async def view_event_participants(query):
    """View event participants."""
    bot_state = load_bot_state()
    participants = bot_state.get("event_participants", [])
    
    if not participants:
        await query.edit_message_text(
            "📄 Event Participants\n\n❌ No participants yet.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
            ]])
        )
        return
    
    participants_text = f"📄 Event Participants ({len(participants)})\n\n"
    
    for i, participant in enumerate(participants[-20:], 1):  # Show last 20
        username = participant.get("username", "Unknown")
        user_id = participant.get("user_id", "Unknown")
        participants_text += f"{i}. {username} (ID: {user_id})\n"
    
    if len(participants) > 20:
        participants_text += f"\n... and {len(participants) - 20} more"
    
    await query.edit_message_text(
        participants_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")
        ]])
    )

async def exchange_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle exchange confirmation from admin."""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        return
    
    exchange_id = query.data.split("_", 2)[2]
    bot_state = load_bot_state()
    
    exchange_info = bot_state.get("pending_exchanges", {}).get(exchange_id)
    
    if not exchange_info:
        await query.edit_message_text("❌ Exchange request not found or already processed.")
        return
    
    # Store exchange info for receipt upload
    context.user_data['pending_receipt'] = exchange_info
    
    await query.edit_message_text(
        f"✅ Exchange approved!\n\n"
        f"Please send the receipt photo now.\n"
        f"👤 User: {exchange_info['username']}\n"
        f"💸 Amount: {exchange_info['amount']} points"
    )

async def exchange_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle exchange cancellation from admin."""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        return
    
    exchange_id = query.data.split("_", 2)[2]
    bot_state = load_bot_state()
    
    exchange_info = bot_state.get("pending_exchanges", {}).get(exchange_id)
    
    if not exchange_info:
        await query.edit_message_text("❌ Exchange request not found or already processed.")
        return
    
    # Refund points to user
    user_id = exchange_info["user_id"]
    amount = exchange_info["amount"]
    
    user_data = get_user_data(user_id)
    update_user_data(user_id, {"points": user_data["points"] + amount})
    
    # Remove from pending exchanges
    del bot_state["pending_exchanges"][exchange_id]
    save_bot_state(bot_state)
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Exchange Request Rejected\n\n"
                 f"Your exchange request for {amount} points has been rejected.\n"
                 f"💰 Points have been refunded to your account.\n"
                 f"💳 Current balance: {user_data['points'] + amount} points"
        )
    except Exception as e:
        logger.error(f"Failed to notify user about rejected exchange: {e}")
    
    await query.edit_message_text(f"❌ Exchange request cancelled. Points refunded to user.")

async def handle_receipt_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle receipt photo upload from admin."""
    if update.effective_user.id != OWNER_ID:
        return
    
    exchange_info = context.user_data.get('pending_receipt')
    
    if not exchange_info:
        await update.message.reply_text("❌ No pending exchange found.")
        return
    
    # Get the photo
    photo = update.message.photo[-1]  # Get highest resolution
    
    user_id = exchange_info["user_id"]
    amount = exchange_info["amount"]
    
    # Send confirmation and receipt to user
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Exchange Completed!\n\n"
                 f"💸 Amount: {amount} points\n"
                 f"📧 Receipt attached below:"
        )
        
        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo.file_id,
            caption="📧 Exchange Receipt"
        )
    except Exception as e:
        logger.error(f"Failed to send confirmation to user: {e}")
    
    # Add to user history
    add_user_history(user_id, "Exchange", f"Exchanged {amount} points")
    
    # Log to group
    username = exchange_info["username"]
    user_data = get_user_data(user_id)
    
    log_message = (
        f"✅ Exchange Completed\n"
        f"👤 {username} (ID: {user_id})\n"
        f"💸 Amount: {amount} points\n"
        f"💰 Total: {user_data['points']} points"
    )
    
    await log_to_group(context, log_message)
    
    # Remove from pending exchanges
    exchange_id = f"{user_id}_{amount}"
    bot_state = load_bot_state()
    bot_state.get("pending_exchanges", {}).pop(exchange_id, None)
    save_bot_state(bot_state)
    
    # Clear admin state
    context.user_data.pop('pending_receipt', None)
    
    await update.message.reply_text(f"✅ Exchange completed successfully!")
