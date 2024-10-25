import openai
from openai import OpenAI
import logging
import time
import requests
import re
from datetime import datetime, timezone
import telegram
from telegram import Update, Bot, error
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
    Application,
)
import asyncio
import os
from dotenv import load_dotenv
from db_handler import create_connection, create_table, insert_message

# Load environment variables
load_dotenv()

# Configure logging for Azure
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Changed to INFO for Azure
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Database setup with Azure path
if 'WEBSITE_SITE_NAME' in os.environ:  # Check if running on Azure
    database = "/home/site/wwwroot/telegram_chat.db"
else:
    database = "telegram_chat.db"

# Initialize database
conn = create_connection(database)
create_table(conn)

# OpenAI setup
openai.api_key = os.getenv('OPENAI_API_KEY_JF')
openai_client = OpenAI(api_key=openai.api_key)

# Your existing configuration
messages_by_chat_id = {}
MAX_MESSAGES = 5
ai_model = "gpt-4"  # Temporarily using gpt-4 while waiting for fine-tune
main_prompt = """Your prompt here"""

# Your existing functions remain the same...
# (Include all your existing functions here)

# Modified main execution for better Azure compatibility
def main():
    try:
        application = ApplicationBuilder().token(
            os.getenv('TELEGRAM_BOT_TOKEN')
        ).build()

        chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
        application.add_handler(chat_handler)
        application.add_handler(CommandHandler('fixfiji', reset_command))
        application.add_handler(CommandHandler('current_version', current_version_command))

        # Start the bot
        print("Starting bot...")
        application.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            time.sleep(10)  # Wait before restarting