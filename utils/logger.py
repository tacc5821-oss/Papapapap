import logging
import asyncio
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from config import LOG_GROUP_ID

# Global variables for rate limiting
last_log_time = {}
log_queue = []
log_lock = asyncio.Lock()

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
    """Send log message to the log group with rate limiting."""
    try:
        # Check rate limiting (max 1 message per 3 seconds)
        current_time = datetime.now()
        if LOG_GROUP_ID in last_log_time:
            time_diff = current_time - last_log_time[LOG_GROUP_ID]
            if time_diff.total_seconds() < 3:
                # Add to queue instead of sending immediately
                async with log_lock:
                    log_queue.append((context, message, current_time))
                return
        
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=message
        )
        last_log_time[LOG_GROUP_ID] = current_time
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        if "flood control" not in str(e).lower():
            logger.error(f"Failed to send log to group: {e}")

async def process_log_queue():
    """Process queued log messages."""
    async with log_lock:
        if not log_queue:
            return
        
        # Process oldest message if enough time has passed
        context, message, timestamp = log_queue[0]
        current_time = datetime.now()
        
        if current_time - timestamp > timedelta(seconds=3):
            try:
                await context.bot.send_message(
                    chat_id=LOG_GROUP_ID,
                    text=message
                )
                last_log_time[LOG_GROUP_ID] = current_time
                log_queue.pop(0)
            except Exception:
                pass  # Ignore errors for queued messages
