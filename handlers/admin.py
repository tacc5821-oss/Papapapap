import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import load_bot_state, save_bot_state, get_user_data, update_user_data, add_user_history, get_all_users
from config import OWNER_ID

logger = logging.getLogger(__name__)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin Panel နှင့် လုပ်ဆောင်ချက်များကို ထိန်းချုပ်ခြင်း"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        await query.edit_message_text("❌ Access denied.")
        return
    
    if query.data == "admin_panel":
        await show_admin_panel(query)
    elif query.data == "admin_edit_balance":
        await admin_edit_balance_start(query, context)
    elif query.data == "admin_view_all_users":
        await view_all_users_list(query)

async def show_admin_panel(query):
    """Admin ပင်မစာမျက်နှာ"""
    bot_state = load_bot_state()
    pending_exchanges = bot_state.get("pending_exchanges", {})
    pending_count = len(pending_exchanges)
    
    admin_text = (
        "🧑‍💼 **Admin Control Panel**\n\n"
        f"⏳ စစ်ဆေးရန် ငွေထုတ်လွှာ: {pending_count} ခု\n"
        "--------------------------\n"
        "Owner အနေဖြင့် အောက်ပါတို့ကို လုပ်ဆောင်နိုင်သည် -"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"📥 Pending Requests ({pending_count})", callback_data="admin_view_pending")],
        [InlineKeyboardButton("⚙️ Edit User Balance (+/-)", callback_data="admin_edit_balance")],
        [InlineKeyboardButton("👥 View All Users", callback_data="admin_view_all_users")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(admin_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- MMK Balance Adjustment Logic ---

async def admin_edit_balance_start(query, context):
    """User ID တောင်းခံခြင်း"""
    context.user_data["admin_waiting_for_uid"] = True
    await query.edit_message_text(
        "📝 **Edit User Balance**\n\n"
        "ငွေပြင်ဆင်လိုသော User ၏ **Telegram ID** ကို ရိုက်ပို့ပေးပါ -"
    )

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner ရိုက်ပို့လိုက်သော စာသားများကို စစ်ဆေးခြင်း"""
    if update.effective_user.id != OWNER_ID: return
    text = update.message.text.strip()

    # Step 1: Handle User ID Input
    if context.user_data.get("admin_waiting_for_uid"):
        if not text.isdigit():
            await update.message.reply_text("❌ ID သည် ဂဏန်းသီးသန့် ဖြစ်ရပါမည်။")
            return
        
        target_uid = int(text)
        target_data = get_user_data(target_uid)
        
        context.user_data["admin_target_uid"] = target_uid
        context.user_data["admin_waiting_for_uid"] = False
        context.user_data["admin_waiting_for_amount"] = True
        
        await update.message.reply_text(
            f"👤 User: {target_data.get('username') or 'No Username'}\n"
            f"💰 Current Balance: {target_data.get('mmk', 0)} MMK\n\n"
            "တိုးလို/လျှော့လိုသော ပမာဏကို ရိုက်ပါ -\n"
            "(ဥပမာ: `10000` တိုးရန် သို့မဟုတ် `-5000` လျှော့ရန်)"
        )
        return

    # Step 2: Handle Amount Adjustment
    if context.user_data.get("admin_waiting_for_amount"):
        try:
            amount_change = int(text)
            target_uid = context.user_data.get("admin_target_uid")
            target_data = get_user_data(target_uid)
            
            new_balance = max(0, target_data.get('mmk', 0) + amount_change)
            update_user_data(target_uid, {"mmk": new_balance})
            add_user_history(target_uid, "Admin Adjustment", f"{amount_change} MMK by Owner")
            
            context.user_data["admin_waiting_for_amount"] = False
            await update.message.reply_text(f"✅ အောင်မြင်ပါသည်။\nBalance အသစ်: {new_balance} MMK")
            
            # Notify User
            try:
                await context.bot.send_message(target_uid, f"📢 Owner မှ သင့် Balance ကို {amount_change} MMK ပြင်ဆင်လိုက်ပါသည်။\nလက်ရှိ: {new_balance} MMK")
            except: pass
        except ValueError:
            await update.message.reply_text("❌ ဂဏန်းအမှန်အတိုင်း ရိုက်ပေးပါ။")

# --- Exchange (Withdrawal) Management ---

async def exchange_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ငွေထုတ်လွှာကို အတည်ပြုရန် Slip တောင်းခြင်း"""
    query = update.callback_query
    exchange_id = query.data.split("_")[2]
    
    bot_state = load_bot_state()
    exchange_info = bot_state.get("pending_exchanges", {}).get(exchange_id)
    
    if not exchange_info:
        await query.edit_message_text("❌ ဤတောင်းဆိုမှုသည် မရှိတော့ပါ။")
        return
        
    context.user_data['pending_receipt_info'] = exchange_info
    context.user_data['pending_exchange_id'] = exchange_id
    
    await query.edit_message_text(
        f"✅ Approved: {exchange_info['amount']} MMK\n"
        f"User: {exchange_info['username']}\n\n"
        "ကျေးဇူးပြု၍ **ငွေလွှဲပြီးကြောင်း Slip ပုံ** ကို ပို့ပေးပါ။"
    )

async def handle_receipt_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin တင်လိုက်သော Slip ကို User ထံ ပို့ပေးခြင်း"""
    if update.effective_user.id != OWNER_ID: return
    
    info = context.user_data.get('pending_receipt_info')
    ex_id = context.user_data.get('pending_exchange_id')
    
    if not info or not update.message.photo: return

    photo = update.message.photo[-1].file_id
    user_id = info['user_id']
    
    # 1. Send to User
    await context.bot.send_message(user_id, f"✅ သင်၏ ငွေထုတ်ယူမှု ({info['amount']} MMK) အောင်မြင်ပါသည်။")
    await context.bot.send_photo(user_id, photo, caption="ငွေလွှဲပြေစာ (Receipt)")
    
    # 2. Cleanup State
    bot_state = load_bot_state()
    if ex_id in bot_state["pending_exchanges"]:
        del bot_state["pending_exchanges"][ex_id]
        save_bot_state(bot_state)
    
    context.user_data.pop('pending_receipt_info', None)
    await update.message.reply_text("✅ Slip ကို User ထံ ပို့ပြီးပါပြီ။")

async def exchange_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ငွေထုတ်လွှာကို ပယ်ဖျက်ပြီး User ထံ ငွေပြန်ထည့်ပေးခြင်း"""
    query = update.callback_query
    exchange_id = query.data.split("_")[2]
    
    bot_state = load_bot_state()
    info = bot_state.get("pending_exchanges", {}).get(exchange_id)
    
    if info:
        user_id = info['user_id']
        refund_amount = info['amount']
        
        user_data = get_user_data(user_id)
        update_user_data(user_id, {"mmk": user_data.get('mmk', 0) + refund_amount})
        
        del bot_state["pending_exchanges"][exchange_id]
        save_bot_state(bot_state)
        
        try:
            await context.bot.send_message(user_id, f"❌ သင်၏ ငွေထုတ်ယူမှု ပယ်ဖျက်ခံရပါသည်။ {refund_amount} MMK ကို Balance ထဲ ပြန်ထည့်ပေးထားပါသည်။")
        except: pass
        
    await query.edit_message_text("❌ ငွေထုတ်လွှာကို ပယ်ဖျက်ပြီး ငွေပြန်အမ်းလိုက်ပါပြီ။")

async def view_all_users_list(query):
    """အသုံးပြုသူအားလုံးကို ကြည့်ရှုခြင်း"""
    users = get_all_users()
    text = f"👥 **Total Users: {len(users)}**\n\n"
    for u in users[:15]: # ပထမ ၁၅ ယောက်ပြရန်
        text += f"🔹 {u.get('username') or 'NoName'} (ID: `{u['user_id']}`) - {u.get('mmk', 0)} MMK\n"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]))
