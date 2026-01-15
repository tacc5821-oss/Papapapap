import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN, OWNER_ID
from database import init_database
from handlers.menu import start, main_menu_callback
# Spin အစား Crash Game handler ကိုသုံးမည်
from handlers.crash_game import crash_game_start, crash_game_bet_handler, cash_out_callback 
from handlers.exchange import exchange_request_callback, exchange_manual_amount_handler
from handlers.jackpot import jackpot_control_callback, jackpot_done_callback
from handlers.admin import (
    admin_callback, 
    exchange_confirm_callback, 
    exchange_cancel_callback,
    handle_receipt_upload # Slip ပို့ရန်
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

    # Add command handlers
    application.add_handler(CommandHandler("start", start))

    # --- User Side Handlers ---
    # Main Menu & Basic Actions
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^(main_menu|history|invite_friends|get_help)$"))
    
    # Crash Game (Spin နေရာမှာ အစားထိုးခြင်း)
    application.add_handler(CallbackQueryHandler(crash_game_start, pattern="^crash_game$"))
    application.add_handler(CallbackQueryHandler(cash_out_callback, pattern="^cash_out$"))

    # Exchange MMK (Amount ရိုက်ထည့်သောစနစ်)
    application.add_handler(CallbackQueryHandler(exchange_request_callback, pattern="^exchange$"))

    # --- Admin/Owner Side Handlers ---
    # Jackpot Control (Event နေရာမှာ အစားထိုးခြင်း)
    application.add_handler(CallbackQueryHandler(jackpot_control_callback, pattern="^jackpot_control$"))
    application.add_handler(CallbackQueryHandler(jackpot_done_callback, pattern="^jackpot_done$"))
    
    # Admin Exchange Approval & Rejection
    application.add_handler(CallbackQueryHandler(exchange_confirm_callback, pattern="^exchange_confirm_"))
    application.add_handler(CallbackQueryHandler(exchange_cancel_callback, pattern="^exchange_cancel_"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # --- Message & Photo Handlers ---
    # User ဆီမှ ဂိမ်းလောင်းကြေး နှင့် Exchange Amount လက်ခံရန်
    # Admin ဆီမှ Slip ပုံ လက်ခံရန်
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_inputs))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))

    logger.info("Bot started successfully with Crash Game & Manual Exchange")
    
    # Run the bot
    application.run_polling(allowed_updates=["message", "callback_query"])

async def handle_all_text_inputs(update, context):
    """စာရိုက်ပို့သမျှကို ခွဲခြားပြီး Handle လုပ်ပေးသည့်နေရာ"""
    user_data = context.user_data
    
    # အကယ်၍ User က လောင်းကြေးရိုက်နေခြင်းဖြစ်လျှင်
    if user_data.get("waiting_for_bet"):
        await crash_game_bet_handler(update, context)
        
    # အကယ်၍ User က Exchange Amount ရိုက်နေခြင်းဖြစ်လျှင်
    elif user_data.get("waiting_for_exchange_amount"):
        await exchange_manual_amount_handler(update, context)

async def handle_receipt_photo(update, context):
    """Admin ဆီမှ Slip ပုံကို လက်ခံပြီး User ဆီ ပို့ပေးခြင်း"""
    if str(update.effective_user.id) == str(OWNER_ID):
        await handle_receipt_upload(update, context)

if __name__ == '__main__':
    main()
