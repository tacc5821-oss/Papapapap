import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_all_users, update_user_data, add_user_history
from config import OWNER_ID

logger = logging.getLogger(__name__)

async def jackpot_control_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner အတွက် Jackpot Control Panel ပြသရန်"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != OWNER_ID:
        await query.message.reply_text("🚫 ဤနေရာကို ဝင်ရောက်ခွင့်မရှိပါ။")
        return

    text = (
        "🎰 **Owner Jackpot Control**\n\n"
        "ဒီခလုတ်ကို နှိပ်လိုက်ရင် လက်ရှိ Bot သုံးနေတဲ့သူတွေထဲက "
        "ကံထူးရှင် (၅) ဦးကို Random ရွေးပြီး တစ်ယောက်ကို ၅၀၀၀ MMK စီ ဆုချီးမြှင့်ပါမယ်။"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔥 Jackpot ဖောက်ပေးမည်", callback_data="jackpot_done")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def jackpot_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jackpot ဖောက်ပေးခြင်း logic"""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != OWNER_ID: return

    all_users = get_all_users()
    if len(all_users) < 1:
        await query.edit_message_text("❌ User မရှိသေးပါ။")
        return

    # လူ (၅) ယောက်ကို Random ရွေးချယ်ခြင်း (ရှိသလောက် လူဦးရေပေါ် မူတည်သည်)
    winner_count = min(5, len(all_users))
    winners = random.sample(all_users, winner_count)
    reward_amount = 5000

    winner_names = []
    for winner in winners:
        user_id = winner['user_id']
        current_mmk = winner.get('mmk', 0)
        
        # ပိုက်ဆံတိုးပေးခြင်း
        update_user_data(user_id, {"mmk": current_mmk + reward_amount})
        add_user_history(user_id, "Jackpot Win", f"Received {reward_amount} MMK")
        
        winner_names.append(f"👤 {winner.get('username') or user_id}")
        
        # ကံထူးရှင်ထံသို့ Message ပို့ပေးခြင်း
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎰 🎉 **Congratulations!**\n\nသင်သည် Owner ၏ Jackpot ကံစမ်းပွဲမှ **{reward_amount} MMK** ကံထူးသွားပါသည်။"
            )
        except Exception as e:
            logger.error(f"Could not send win message to {user_id}: {e}")

    result_text = (
        "✅ **Jackpot ပေါက်သူများစာရင်း**\n\n" + 
        "\n".join(winner_names) + 
        f"\n\nစုစုပေါင်း {winner_count} ဦးကို {reward_amount} MMK စီ ချီးမြှင့်ပြီးပါပြီ။"
    )

    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]))
