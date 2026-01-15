import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_user_data, update_user_data, add_user_history

logger = logging.getLogger(__name__)

async def crash_game_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဂိမ်းစတင်ခြင်းနှင့် Multiplier တက်ခြင်း Logic"""
    user = update.effective_user
    user_data = get_user_data(user.id)
    
    # လောင်းကြေးပမာဏကို context ထဲမှယူခြင်း
    try:
        bet_amount = int(context.user_data.get("current_bet", 0))
    except:
        await update.message.reply_text("❌ လောင်းကြေးသတ်မှတ်မှု မှားယွင်းနေပါသည်။")
        return

    # ပိုက်ဆံစစ်ဆေးခြင်း
    if user_data.get('mmk', 0) < bet_amount:
        await update.message.reply_text("❌ လက်ကျန်ငွေ မလုံလောက်ပါ။")
        return

    # ဂိမ်းအခြေအနေသတ်မှတ်ခြင်း
    context.user_data["is_playing"] = True
    update_user_data(user.id, {"mmk": user_data['mmk'] - bet_amount})
    
    # Crash Point ကို Random သတ်မှတ်ခြင်း (1.2 မှ 10.0 ကြား)
    crash_point = round(random.uniform(1.2, 10.0), 1)
    
    # +0.2 စီတိုးမည့် Multipliers စာရင်း
    multipliers = [
        (1.0, "🥚"), (1.2, "🐣"), (1.4, "🐥"), (1.6, "🐤"), (1.8, "🐦"),
        (2.0, "🐧"), (2.2, "🕊️"), (2.4, "🦅"), (2.6, "🦆"), (2.8, "🦢"),
        (3.0, "🦉"), (3.2, "🦚"), (3.4, "🦜"), (3.6, "🦄"), (3.8, "🦊"),
        (4.0, "🦁"), (4.2, "🐯"), (4.4, "🦄"), (4.6, "🦋"), (4.8, "🐝"),
        (5.0, "🐲"), (5.2, "🐳"), (5.4, "🐘"), (5.6, "🦒"), (5.8, "🦓"),
        (6.0, "🐆"), (6.2, "🐎"), (6.4, "🦌"), (6.6, "🐕"), (6.8, "🐈"),
        (7.0, "🐿️"), (7.2, "🐇"), (7.4, "🐹"), (7.6, "🐼"), (7.8, "🐨"),
        (8.0, "🐻"), (8.2, "🐮"), (8.4, "🐷"), (8.6, "🐸"), (8.8, "🐵"),
        (9.0, "🌛"), (9.2, "🌟"), (9.4, "🌌"), (9.6, "🛰️"), (9.8, "🛸"),
        (10.0, "🚀")
    ]

    game_msg = await update.message.reply_text("🚀 ဂိမ်းစတင်နေပါပြီ...")

    for rate, emoji in multipliers:
        # Cash Out နှိပ်လိုက်လျှင် Loop ကိုရပ်ရန်
        if not context.user_data.get("is_playing"):
            return

        # Crash Point ရောက်သွားလျှင် (ရှုံးလျှင်)
        if rate >= crash_point:
            context.user_data["is_playing"] = False
            await game_msg.edit_text(f"💥 **BOOM! {rate}x** မှာ ပေါက်ကွဲသွားပါပြီ။\n💸 သင် {bet_amount} MMK ရှုံးနိမ့်သွားပါသည်။")
            return

        # Multiplier တက်နေစဉ် Message ကို Update လုပ်ခြင်း
        await game_msg.edit_text(
            f"📈 **Multiplier: {rate}x {emoji}**\n"
            f"💰 အနိုင်ရရှိနိုင်ခြေ: {int(bet_amount * rate)} MMK",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💰 Cash Out", callback_data=f"cash_out_{rate}")
            ]])
        )
        
        # Multiplier တက်သည့်အရှိန် (1.2 စက္ကန့် စောင့်ခြင်း)
        await asyncio.sleep(1.2)

async def cash_out_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cash Out ခလုတ်နှိပ်သည့်အခါ အလုပ်လုပ်မည့် Function"""
    query = update.callback_query
    
    # ဂိမ်းကစားနေဆဲဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if not context.user_data.get("is_playing"):
        await query.answer("❌ ဂိမ်းက ပြီးဆုံးသွားပါပြီ။", show_alert=True)
        return

    # ဂိမ်းကိုချက်ချင်းရပ်ခြင်း
    context.user_data["is_playing"] = False
    await query.answer()

    # Data ခွဲထုတ်ခြင်း (cash_out_1.4 ဆိုလျှင် 1.4 ကိုယူခြင်း)
    try:
        rate = float(query.data.split("_")[2])
        bet_amount = context.user_data.get("current_bet", 0)
        win_amount = int(bet_amount * rate)
        
        user_id = query.from_user.id
        user_data = get_user_data(user_id)
        
        # ပိုက်ဆံအသစ်တွက်ချက်ပြီး Update လုပ်ခြင်း
        new_balance = user_data.get('mmk', 0) + win_amount
        update_user_data(user_id, {"mmk": new_balance})
        add_user_history(user_id, "Crash Win", f"Won {win_amount} MMK at {rate}x")

        await query.edit_message_text(
            f"✅ **Cash Out အောင်မြင်ပါသည်။**\n\n"
            f"📈 Multiplier: {rate}x\n"
            f"💰 အနိုင်ရရှိငွေ: {win_amount} MMK\n"
            f"💵 လက်ရှိလက်ကျန်: {new_balance} MMK",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")
            ]])
        )
    except Exception as e:
        logger.error(f"Cashout error: {e}")
        await query.message.reply_text("❌ အမှားအယွင်းတစ်ခု ဖြစ်သွားပါသည်။")
