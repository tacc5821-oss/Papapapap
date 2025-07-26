import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, load_bot_state, save_bot_state, add_user_history
from config import EXCHANGE_AMOUNTS, OWNER_ID
from utils.logger import log_to_group

logger = logging.getLogger(__name__)

async def exchange_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle exchange button callback."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    exchange_text = (
        f"📤 Exchange Points\n\n"
        f"💰 Your Points: {user_data['points']}\n\n"
        f"Choose amount to exchange:"
    )
    
    keyboard = []
    for amount in EXCHANGE_AMOUNTS:
        if user_data['points'] >= amount:
            keyboard.append([InlineKeyboardButton(f"💸 {amount} Points", callback_data=f"exchange_{amount}")])
        else:
            keyboard.append([InlineKeyboardButton(f"❌ {amount} Points (Insufficient)", callback_data="insufficient")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        exchange_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def exchange_amount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle exchange amount selection."""
    query = update.callback_query
    
    if query.data == "insufficient":
        await query.answer("❌ Insufficient points for this exchange!", show_alert=True)
        return
    
    # Handle non-numeric callback data
    if not query.data.startswith("exchange_") or len(query.data.split("_")) < 2:
        await query.answer("❌ Invalid selection!", show_alert=True)
        return
    
    try:
        amount = int(query.data.split("_")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Invalid amount selection!", show_alert=True)
        return
    
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    # Check if user has enough points
    if user_data['points'] < amount:
        await query.edit_message_text(
            f"❌ Insufficient Points\n\n"
            f"💰 Your Points: {user_data['points']}\n"
            f"📤 Required: {amount}\n\n"
            f"Earn more points by spinning!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Create exchange request
    bot_state = load_bot_state()
    if "pending_exchanges" not in bot_state:
        bot_state["pending_exchanges"] = {}
    
    exchange_id = f"{user.id}_{amount}"
    bot_state["pending_exchanges"][exchange_id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "amount": amount,
        "remaining_points": user_data['points'] - amount
    }
    save_bot_state(bot_state)
    
    # Deduct points temporarily
    update_user_data(user.id, {"points": user_data['points'] - amount})
    
    # Send request to owner
    await send_exchange_request_to_owner(context, user, amount, user_data['points'] - amount, exchange_id)
    
    # Notify user
    await query.edit_message_text(
        f"📤 Exchange Request Sent\n\n"
        f"💸 Amount: {amount} points\n"
        f"💰 Remaining: {user_data['points'] - amount} points\n\n"
        f"⏳ Please wait for admin approval.\n"
        f"You will receive confirmation once processed.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
        ]])
    )

async def send_exchange_request_to_owner(context, user, amount, remaining_points, exchange_id):
    """Send exchange request to owner."""
    username = f"@{user.username}" if user.username else user.first_name
    
    request_message = (
        f"📤 Exchange Request\n"
        f"👤 {username} (ID: {user.id})\n"
        f"🔄 Request: {amount} points\n"
        f"💰 Remaining: {remaining_points} points"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"exchange_confirm_{exchange_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"exchange_cancel_{exchange_id}")
        ]
    ]
    
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=request_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Failed to send exchange request to owner: {e}")
