import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, add_user_history
from config import OWNER_ID, LOG_GROUP_ID

logger = logging.getLogger(__name__)

async def crash_game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = get_user_data(query.from_user.id)
    context.user_data["waiting_for_bet"] = True
    await query.edit_message_text(
        f"🚀 **Crash Game**\n\n💰 Balance: {user_data.get('mmk', 0)} MMK\n"
        f"လောင်းကြေးပမာဏ ရိုက်ပို့ပေးပါ -",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
    )

async def crash_game_bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_bet"): return
    bet_text = update.message.text.strip()
    if not bet_text.isdigit():
        await update.message.reply_text("❌ ဂဏန်းပဲရိုက်ပါ။")
        return
    
    bet_amount = int(bet_text)
    user = update.effective_user
    user_data = get_user_data(user.id)
    
    if user_data.get('mmk', 0) < bet_amount:
        await update.message.reply_text("❌ ပိုက်ဆံမလုံလောက်ပါ။")
        return

    context.user_data["waiting_for_bet"] = False
    context.user_data["is_playing"] = True
    context.user_data["current_bet"] = bet_amount
    update_user_data(user.id, {"mmk": user_data.get('mmk') - bet_amount})
    
    multipliers = [(1.0, "🥚"), (1.1, "🐣"), (1.3, "🐥"), (1.6, "🦅"), (2.0, "✈️"), (2.5, "🚀"), (3.2, "🛸"), (4.0, "☄️")]
    crash_point = round(random.uniform(1.1, 4.0), 1)
    game_msg = await update.message.reply_text("ဂိမ်းစတင်ပါပြီ... ⏳")
    
    for rate, emoji in multipliers:
        if not context.user_data.get("is_playing"): break
        if rate >= crash_point:
            context.user_data["is_playing"] = False
            await game_msg.edit_text(f"💥 BOOM! {rate}x မှာ ပေါက်ကွဲသွားသည်။")
            return
        
        await game_msg.edit_text(
            f"📈 Multiplier: {rate}x {emoji}\n💰 Win: {int(bet_amount * rate)} MMK",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💰 Cash Out ({rate}x)", callback_data=f"cash_out_{rate}")]])
        )
        await asyncio.sleep(1.2)

async def cash_out_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not context.user_data.get("is_playing"): return
    context.user_data["is_playing"] = False
    rate = float(query.data.split("_")[2])
    bet_amount = context.user_data.get("current_bet")
    win_amount = int(bet_amount * rate)
    user_data = get_user_data(query.from_user.id)
    update_user_data(query.from_user.id, {"mmk": user_data.get('mmk', 0) + win_amount})
    await query.edit_message_text(f"✅ Cash Out အောင်မြင်သည်။\n💰 {win_amount} MMK ရရှိပါသည်။")
