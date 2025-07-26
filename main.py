import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN, OWNER_ID, LOG_GROUP_ID
from database import init_database
from handlers.menu import start, main_menu_callback
from handlers.spin import spin_callback
from handlers.exchange import exchange_callback, exchange_amount_callback
from handlers.event import event_callback, event_done_callback
from handlers.admin import admin_callback, event_confirm_callback, event_cancel_callback, exchange_confirm_callback, exchange_cancel_callback
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

    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^(main_menu|my_points|history)$"))
    application.add_handler(CallbackQueryHandler(spin_callback, pattern="^spin$"))
    application.add_handler(CallbackQueryHandler(exchange_callback, pattern="^exchange$"))
    application.add_handler(CallbackQueryHandler(exchange_amount_callback, pattern="^exchange_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(event_callback, pattern="^event$"))
    application.add_handler(CallbackQueryHandler(event_done_callback, pattern="^event_done$"))
    
    # Admin handlers
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(admin_|event_limit_)"))
    application.add_handler(CallbackQueryHandler(event_confirm_callback, pattern="^event_confirm_"))
    application.add_handler(CallbackQueryHandler(event_cancel_callback, pattern="^event_cancel_"))
    application.add_handler(CallbackQueryHandler(exchange_confirm_callback, pattern="^exchange_confirm_"))
    application.add_handler(CallbackQueryHandler(exchange_cancel_callback, pattern="^exchange_cancel_"))

    # Add message handlers for admin functions
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_messages))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))

    logger.info("Bot started successfully")
    
    # Run the bot
    application.run_polling(allowed_updates=["message", "callback_query"])

async def handle_admin_messages(update, context):
    """Handle admin messages for event creation."""
    from handlers.admin import handle_event_channels
    await handle_event_channels(update, context)

async def handle_receipt_photo(update, context):
    """Handle receipt photos from admin."""
    from handlers.admin import handle_receipt_upload
    await handle_receipt_upload(update, context)

if __name__ == '__main__':
    main()
