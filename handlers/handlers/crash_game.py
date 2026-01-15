import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, add_user_history
from config import OWNER_ID, LOG_GROUP_ID
from utils.logger import log_to_group

logger = logging.getLogger(__name__)

async def crash_game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဂိမ်းစတင်ရန် လောင်းကြေးတောင်းသည့်အပိုင်း"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    # User ကို လောင်းကြေးရိုက်ခိုင်းရန် State မှတ်ခြင်း
    context.user_data["waiting_for_bet"] = True
    
    await query.edit_message_text(
        f"🚀 **Crash Game (Emoji Multiplier)**\n\n"
        f"💰 Your Balance: {user_data.get('mmk', 0)} MMK\n\n"
        f"လောင်းလိုသော ပမာဏကို စာရိုက်ပို့ပေးပါ (ဥပမာ - 500)"
    )

async def crash_game_bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ရိုက်လိုက်သော လောင်းကြေးကို စစ်ဆေးပြီး ဂိမ်းစတင်ခြင်း"""
    if not context.user_data.get("waiting_for_bet"):
        return

    bet_text = update.message.text.strip()
    if not bet_text.isdigit():
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ ဂဏန်းသီးသန့်သာ ရိုက်ပေးပါ။")
        return

    bet_amount = int(bet_text)
    user = update.effective_user
    user_data = get_user_data(user.id)
    
    if user_data.get('mmk', 0) < bet_amount:
        await update.message.reply_text("❌ လက်ကျန်ငွေ မလုံလောက်ပါ။")
        return

    context.user_data["waiting_for_bet"] = False
    context.user_data["is_playing"] = True
    context.user_data["current_bet"] = bet_amount

    # Financial Logic: 10% Owner Profit ဖယ်ထုတ်ခြင်း
    owner_profit = int(bet_amount * 0.10)
    play_pool_amount = bet_amount - owner_profit
    
    # Balance နုတ်ခြင်း
    update_user_data(user.id, {"mmk": user_data.get('mmk') - bet_amount})
    
    # Multiplier အဆင့်ဆင့်နှင့် Emoji များ
    multipliers = [
        (1.0, "🥚"), (1.1, "🐣"), (1.3, "🐥"), (1.6, "🦅"), 
        (2.0, "✈️"), (2.5, "🚀"), (3.2, "🛸"), (4.0, "☄️")
    ]
    
    # Random Crash Point သတ်မှတ်ခြင်း
    crash_point = round(random.uniform(1.0, 4.2), 1)
    
    game_msg = await update.message.reply_text("ဂိမ်းစတင်နေပါပြီ... ⏳")
    
    current_multiplier = 1.0
    for rate, emoji in multipliers:
        if not context.user_data.get("is_playing"): # User က Cash Out နှိပ်လိုက်လျှင်
            break
            
        if rate >= crash_point: # Boom ဖြစ်သွားလျှင်
            context.user_data["is_playing"] = False
            await game_msg.edit_text(f"💥 **BOOM! {rate}x** မှာ ပေါက်ကွဲသွားပါတယ်။\n\nသင် {bet_amount} MMK ရှုံးသွားပါပြီ။")
            add_user_history(user.id, "Crash Game", f"Lost {bet_amount} MMK (Crash at {rate}x)")
            return

        current_multiplier = rate
        keyboard = [[InlineKeyboardButton(f"💰 CASH OUT ({rate}x)", callback_data=f"cash_out_{rate}")]]
        
        await game_msg.edit_text(
            f"📈 Multiplier: **{rate}x** {emoji}\n"
            f"💵 Win: {int(bet_amount * rate)} MMK\n\n"
            f"ပေါက်ကွဲခြင်း မဖြစ်ခင် Cash Out နှိပ်ပါ!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await asyncio.sleep(1.2) # အချိန်တိုအတွင်း မြန်မြန်တက်ရန်

async def cash_out_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ငွေထုတ်ယူသည့်အပိုင်း"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get("is_playing"):
        return

    context.user_data["is_playing"] = False
    rate = float(query.data.split("_")[2])
    bet_amount = context.user_data.get("current_bet")
    win_amount = int(bet_amount * rate)
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    # Balance ထဲ အနိုင်ငွေ ပေါင်းထည့်ခြင်း
    new_balance = user_data.get('mmk', 0) + win_amount
    update_user_data(user.id, {"mmk": new_balance})
    
    await query.edit_message_text(
        f"✅ **CASH OUT SUCCESS!**\n\n"
        f"💰 You won: {win_amount} MMK\n"
        f"📈 Rate: {rate}x\n"
        f"💳 New Balance: {new_balance} MMK",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Play Again", callback_data="crash_game"),
            InlineKeyboardButton("🔙 Menu", callback_data="main_menu")
        ]])
    )
    
    add_user_history(user.id, "Crash Game", f"Won {win_amount} MMK at {rate}x")
    
    # Admin Log သို့ ပို့ခြင်း (၅ ကြိမ်လျှင် တစ်ခါ)
    played_count = user_data.get("total_games_played", 0) + 1
    update_user_data(user.id, {"total_games_played": played_count})
    
    if played_count % 5 == 0:
        await log_to_group(context, f"🎮 **Crash Game Log**\n👤 {user.first_name}\n🎯 Total Played: {played_count}\n💰 Balance: {new_balance} MMK")
