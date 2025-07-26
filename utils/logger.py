import logging
from telegram.ext import ContextTypes
from config import LOG_GROUP_ID

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    
    # Reduce telegram library logging
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

async def log_to_group(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send log message to the log group."""
    try:
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=message
        )
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to send log to group: {e}")
