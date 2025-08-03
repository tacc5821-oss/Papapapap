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
        f"📤 Exchange MMK\n\n"
        f"💰 Your MMK: {user_data.get('mmk', 0)} MMK\n\n"
        f"Choose amount to exchange:"
    )
    
    keyboard = []
    user_mmk = user_data.get('mmk', 0)
    for amount in EXCHANGE_AMOUNTS:
        if user_mmk >= amount:
            keyboard.append([InlineKeyboardButton(f"💸 {amount} MMK", callback_data=f"exchange_{amount}")])
        else:
            keyboard.append([InlineKeyboardButton(f"❌ {amount} MMK (Insufficient)", callback_data="insufficient")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    await query.edit_message_text(
        exchange_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def exchange_amount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle exchange amount selection."""
    query = update.callback_query
    
    if query.data == "insufficient":
        await query.answer("❌ Insufficient MMK for this exchange!", show_alert=True)
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
    
    # Check if user has enough MMK
    user_mmk = user_data.get('mmk', 0)
    if user_mmk < amount:
        await query.edit_message_text(
            f"❌ Insufficient MMK\n\n"
            f"💰 Your MMK: {user_mmk} MMK\n"
            f"📤 Required: {amount} MMK\n\n"
            f"Earn more MMK by spinning!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Store amount temporarily and show payment method selection
    context.user_data['pending_exchange_amount'] = amount
    await show_payment_method_selection(query, amount)

async def show_payment_method_selection(query, amount):
    """Show payment method selection."""
    payment_text = (
        f"💳 Select Payment Method\n\n"
        f"💸 Exchange Amount: {amount} MMK\n\n"
        f"Choose your preferred payment method:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📱 KPay", callback_data=f"payment_kpay_{amount}")],
        [InlineKeyboardButton("🌊 Wave Money", callback_data=f"payment_wave_{amount}")],
        [InlineKeyboardButton("🔙 Back to Exchange", callback_data="exchange")]
    ]
    
    await query.edit_message_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_payment_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract payment method and amount
    parts = query.data.split("_")
    if len(parts) < 3:
        await query.answer("❌ Invalid selection!", show_alert=True)
        return
    
    payment_method = parts[1]  # kpay or wave
    amount = int(parts[2])
    
    # Store payment method
    context.user_data['pending_payment_method'] = payment_method
    context.user_data['pending_exchange_amount'] = amount
    
    method_name = "KPay" if payment_method == "kpay" else "Wave Money"
    
    await query.edit_message_text(
        f"📱 {method_name} Selected\n\n"
        f"💸 Amount: {amount} MMK\n\n"
        f"Please send your payment information:\n"
        f"📞 Phone Number: (e.g., 09xxxxxxxxx)\n"
        f"👤 Account Name: (Your full name)\n\n"
        f"Example:\n"
        f"09123456789\n"
        f"John Doe\n\n"
        f"Type /cancel to cancel exchange.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="exchange")
        ]])
    )

async def handle_payment_info_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment info input from user."""
    if not context.user_data.get('pending_exchange_amount') or not context.user_data.get('pending_payment_method'):
        return
    
    user = update.effective_user
    text = update.message.text.strip()
    
    if text == "/cancel":
        context.user_data.pop('pending_exchange_amount', None)
        context.user_data.pop('pending_payment_method', None)
        await update.message.reply_text("❌ Exchange cancelled.")
        return
    
    # Parse payment info (expecting phone and name on separate lines)
    lines = text.split('\n')
    if len(lines) < 2:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Please send both phone number and name:\n"
            "09123456789\n"
            "John Doe"
        )
        return
    
    phone = lines[0].strip()
    name = lines[1].strip()
    
    # Basic phone validation
    if not phone.startswith('09') or len(phone) != 11:
        await update.message.reply_text(
            "❌ Invalid phone number format!\n"
            "Please use format: 09xxxxxxxxx"
        )
        return
    
    if len(name) < 2:
        await update.message.reply_text(
            "❌ Please provide a valid name!"
        )
        return
    
    # Get stored data
    amount = context.user_data['pending_exchange_amount']
    payment_method = context.user_data['pending_payment_method']
    method_name = "KPay" if payment_method == "kpay" else "Wave Money"
    
    # Create exchange request
    await create_exchange_request(update, context, user, amount, payment_method, method_name, phone, name)

async def create_exchange_request(update, context, user, amount, payment_method, method_name, phone, name):
    """Create exchange request with payment details."""
    user_data = get_user_data(user.id)
    
    # Check MMK again
    user_mmk = user_data.get('mmk', 0)
    if user_mmk < amount:
        await update.message.reply_text(
            f"❌ Insufficient MMK!\n"
            f"💰 Your MMK: {user_mmk} MMK\n"
            f"📤 Required: {amount} MMK"
        )
        return
    
    # Create exchange request
    bot_state = load_bot_state()
    if "pending_exchanges" not in bot_state:
        bot_state["pending_exchanges"] = {}
    
    exchange_id = f"{user.id}_{amount}_{payment_method}"
    bot_state["pending_exchanges"][exchange_id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "amount": amount,
        "payment_method": method_name,
        "phone": phone,
        "account_name": name,
        "remaining_mmk": user_mmk - amount
    }
    save_bot_state(bot_state)
    
    # Deduct MMK temporarily
    update_user_data(user.id, {"mmk": user_mmk - amount})
    
    # Send enhanced request to owner
    await send_enhanced_exchange_request_to_owner(context, user, amount, payment_method, method_name, phone, name, user_mmk - amount, exchange_id)
    
    # Clear user data
    context.user_data.pop('pending_exchange_amount', None)
    context.user_data.pop('pending_payment_method', None)
    
    # Notify user
    await update.message.reply_text(
        f"✅ Exchange Request Sent!\n\n"
        f"💸 Amount: {amount} MMK\n"
        f"💳 Method: {method_name}\n"
        f"📞 Phone: {phone}\n"
        f"👤 Name: {name}\n"
        f"💰 Remaining: {user_mmk - amount} MMK\n\n"
        f"⏳ Please wait for admin approval.\n"
        f"You will receive confirmation once processed."
    )

async def send_enhanced_exchange_request_to_owner(context, user, amount, payment_method, method_name, phone, name, remaining_mmk, exchange_id):
    """Send enhanced exchange request to owner with payment details."""
    username = f"@{user.username}" if user.username else user.first_name
    
    request_message = (
        f"📤 Exchange Request\n\n"
        f"👤 User: {username} (ID: {user.id})\n"
        f"💸 Amount: {amount} MMK\n"
        f"💳 Method: {method_name}\n"
        f"📞 Phone: {phone}\n"
        f"👤 Name: {name}\n"
        f"💰 Remaining: {remaining_mmk} MMK"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"exchange_confirm_{exchange_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"exchange_cancel_{exchange_id}")
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

async def send_exchange_request_to_owner(context, user, amount, remaining_mmk, exchange_id):
    """Send exchange request to owner."""
    username = f"@{user.username}" if user.username else user.first_name
    
    request_message = (
        f"📤 Exchange Request\n"
        f"👤 {username} (ID: {user.id})\n"
        f"🔄 Request: {amount} MMK\n"
        f"💰 Remaining: {remaining_mmk} MMK"
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
