import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, load_bot_state, save_bot_state
from config import OWNER_ID

logger = logging.getLogger(__name__)

async def exchange_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ငွေထုတ်ရန် ခလုတ်နှိပ်သည့်အခါ Amount တောင်းခြင်း"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    # User ကို Amount ရိုက်ခိုင်းရန် State မှတ်ခြင်း
    context.user_data['waiting_for_exchange_amount'] = True
    
    exchange_text = (
        f"📤 **Exchange MMK**\n\n"
        f"💰 Your MMK: {user_data.get('mmk', 0)} MMK\n\n"
        f"ထုတ်ယူလိုသော ပမာဏကို စာရိုက်ပို့ပေးပါ (ဂဏန်းသီးသန့်) -"
    )
    
    await query.edit_message_text(
        exchange_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
        ]])
    )

async def exchange_manual_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ရိုက်ပို့လိုက်သော Amount ကို စစ်ဆေးပြီး Payment Method ပြခြင်း"""
    if not context.user_data.get('waiting_for_exchange_amount'):
        return

    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ ဂဏန်းသီးသန့်သာ ရိုက်ပေးပါ။")
        return
        
    amount = int(text)
    user = update.effective_user
    user_data = get_user_data(user.id)
    user_mmk = user_data.get('mmk', 0)

    if user_mmk < amount:
        await update.message.reply_text(
            f"❌ လက်ကျန်ငွေ မလုံလောက်ပါ\n💰 Your MMK: {user_mmk} MMK\n📤 Required: {amount} MMK"
        )
        return

    # Amount မှန်ကန်ပါက Payment Method ရွေးခိုင်းမည်
    context.user_data['waiting_for_exchange_amount'] = False
    context.user_data['pending_exchange_amount'] = amount
    
    keyboard = [
        [InlineKeyboardButton("📱 KPay", callback_data=f"payment_kpay_{amount}")],
        [InlineKeyboardButton("🌊 Wave Money", callback_data=f"payment_wave_{amount}")],
        [InlineKeyboardButton("🔙 Back", callback_data="exchange")]
    ]
    
    await update.message.reply_text(
        f"💳 **Select Payment Method**\n\n💸 Amount: {amount} MMK\nငွေလက်ခံမည့် နည်းလမ်းကို ရွေးချယ်ပါ -",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_payment_method_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Payment Method ရွေးပြီးနောက် ဖုန်းနံပါတ် တောင်းခြင်း"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    payment_method = parts[1]
    amount = int(parts[2])
    
    context.user_data['pending_payment_method'] = payment_method
    method_name = "KPay" if payment_method == "kpay" else "Wave Money"
    
    await query.edit_message_text(
        f"📱 {method_name} Selected\n\n💸 Amount: {amount} MMK\n\n"
        f"အောက်ပါအတိုင်း အချက်အလက်ပို့ပေးပါ -\n"
        f"📞 Phone Number: 09xxxxxxxxx\n"
        f"👤 Account Name: Your Name\n\n"
        f"Example:\n09123456789\nJohn Doe\n\n"
        f"ပယ်ဖျက်ရန် /cancel ကိုရိုက်ပါ။",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="exchange")]])
    )

async def handle_payment_info_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ပို့လိုက်သော ဖုန်းနံပါတ်နှင့် နာမည်ကို လက်ခံခြင်း"""
    if not context.user_data.get('pending_exchange_amount'):
        return
    
    user = update.effective_user
    text = update.message.text.strip()
    
    if text == "/cancel":
        context.user_data.clear()
        await update.message.reply_text("❌ Exchange cancelled.")
        return
    
    lines = text.split('\n')
    if len(lines) < 2:
        await update.message.reply_text("❌ Format မှားနေပါသည်။ ဖုန်းနံပါတ်နှင့် နာမည်ကို တစ်ကြောင်းစီ ခွဲရိုက်ပေးပါ။")
        return
    
    phone, name = lines[0].strip(), lines[1].strip()
    amount = context.user_data['pending_exchange_amount']
    payment_method = context.user_data['pending_payment_method']
    method_name = "KPay" if payment_method == "kpay" else "Wave Money"

    # Create request and send to Owner
    await create_exchange_request(update, context, user, amount, payment_method, method_name, phone, name)

async def create_exchange_request(update, context, user, amount, payment_method, method_name, phone, name):
    user_data = get_user_data(user.id)
    user_mmk = user_data.get('mmk', 0)
    
    exchange_id = f"{user.id}_{amount}_{payment_method}"
    bot_state = load_bot_state()
    if "pending_exchanges" not in bot_state: bot_state["pending_exchanges"] = {}
    
    bot_state["pending_exchanges"][exchange_id] = {
        "user_id": user.id, "amount": amount, "payment_method": method_name,
        "phone": phone, "account_name": name
    }
    save_bot_state(bot_state)
    
    # Balance ကို ယာယီနုတ်ထားခြင်း
    update_user_data(user.id, {"mmk": user_mmk - amount})
    
    # Admin ထံ တောင်းဆိုမှု ပို့ခြင်း
    username = f"@{user.username}" if user.username else user.first_name
    admin_msg = (
        f"📤 **New Exchange Request**\n\n"
        f"👤 User: {username} ({user.id})\n"
        f"💸 Amount: {amount} MMK\n💳 Method: {method_name}\n"
        f"📞 Phone: {phone}\n👤 Name: {name}"
    )
    
    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"exchange_confirm_{exchange_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"exchange_cancel_{exchange_id}")
    ]]
    
    await context.bot.send_message(chat_id=OWNER_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data.clear()
    await update.message.reply_text("✅ Request Sent! Admin အတည်ပြုချက်ကို စောင့်ပေးပါ။")
