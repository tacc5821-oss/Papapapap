import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext import ContextTypes
from config import BOT_TOKEN, OWNER_ID
from database import init_database
# handlers.menu မှ လိုအပ်သော function များအားလုံးကို import လုပ်ထားပါသည်
from handlers.menu import start, main_menu_callback, show_my_points, show_history, show_invite_friends, show_help_options 
from handlers.crash_game import crash_game_start, crash_game_bet_handler, cash_out_callback 
from handlers.exchange import exchange_callback, exchange_manual_amount_handler, handle_payment_method_selection, handle_payment_info_message
from handlers.jackpot import jackpot_control_callback, jackpot_done_callback
from handlers.admin import (
    admin_callback, 
    exchange_confirm_callback, 
    exchange_cancel_callback,
    handle_receipt_upload
)
from utils.logger import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize database
    init_database()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Add command handlers ---
    application.add_handler(CommandHandler("start", start))

    # --- User Side Handlers ---
    # Main Menu & Basic Actions (Pattern များကို ခွဲခြားသတ်မှတ်ထားပါသည်)
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(show_my_points, pattern="^my_points$"))
    application.add_handler(CallbackQueryHandler(show_history, pattern="^history$"))
    application.add_handler(CallbackQueryHandler(show_invite_friends, pattern="^invite_friends$"))
    application.add_handler(CallbackQueryHandler(show_help_options, pattern="^get_help$"))
    
    # Crash Game
    application.add_handler(CallbackQueryHandler(crash_game_start, pattern="^crash_game$"))
    application.add_handler(CallbackQueryHandler(cash_out_callback, pattern="^cash_out_")) # pattern ကို အနောက်မှာ rate ပါနိုင်ရန် _ ထည့်ထားပါသည်

    # Exchange MMK (စနစ်သစ်နှင့် ကိုက်ညီအောင် ပြင်ဆင်ထားပါသည်)
    application.add_handler(CallbackQueryHandler(exchange_callback, pattern="^exchange$"))
    application.add_handler(CallbackQueryHandler(handle_payment_method_selection, pattern="^payment_"))

    # --- Admin/Owner Side Handlers ---
    application.add_handler(CallbackQueryHandler(jackpot_control_callback, pattern="^jackpot_control$"))
    application.add_handler(CallbackQueryHandler(jackpot_done_callback, pattern="^jackpot_done$"))
    application.add_handler(CallbackQueryHandler(exchange_confirm_callback, pattern="^exchange_confirm_"))
    application.add_handler(CallbackQueryHandler(exchange_cancel_callback, pattern="^exchange_cancel_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # --- Message & Photo Handlers ---
    # စာသားရိုက်ပို့သမျှကို handle_all_text_inputs ဖြင့် ဖမ်းယူပါသည်
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_inputs))
    # Admin ထံမှ Slip ပုံကို ဖမ်းယူပါသည်
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))

    logger.info("Bot started successfully with Crash Game & Manual Exchange")
    
    # Run the bot
    application.run_polling(allowed_updates=["message", "callback_query"])

async def handle_all_text_inputs(update, context):
    """စာရိုက်ပို့သမျှကို User State အလိုက် ခွဲခြားပေးခြင်း"""
    user_data = context.user_data
    
    # 1. Crash Game လောင်းကြေး စစ်ဆေးခြင်း
    if user_data.get("waiting_for_bet"):
        await crash_game_bet_handler(update, context)
        
    # 2. Exchange Amount စစ်ဆေးခြင်း
    elif user_data.get("waiting_for_exchange_amount"):
        await exchange_manual_amount_handler(update, context)
        
    # 3. Payment Info (Phone/Name) စစ်ဆေးခြင်း
    elif user_data.get("pending_exchange_amount"):
        await handle_payment_info_message(update, context)

async def handle_receipt_photo(update, context):
    """Admin ဆီမှ Slip ပုံကို လက်ခံပြီး သက်ဆိုင်ရာ User ထံ ပို့ပေးခြင်း"""
    # Owner ID စစ်ဆေးခြင်း (လုံခြုံရေးအရ)
    if str(update.effective_user.id) == str(OWNER_ID):
        await handle_receipt_upload(update, context)

if __name__ == '__main__':
    main()
