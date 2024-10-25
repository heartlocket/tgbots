import sys
import logging

# Force immediate logging
print("Bot starting...", flush=True)
sys.stdout.flush()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/LogFiles/application.log')
    ]
)

# Test log at the very start
logger.info("Application starting...")
print("Testing stdout...", flush=True)

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

# Initialize logging with more detail
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Changed from WARNING to INFO for debugging
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Print environment variables (first 5 chars only for security)
print("Checking environment variables...")
print(f"Bot token present: {'TELEGRAM_BOT_TOKEN' in os.environ}")
print(f"OpenAI key present: {'OPENAI_API_KEY_JF' in os.environ}")
if 'TELEGRAM_BOT_TOKEN' in os.environ:
    print(f"Bot token starts with: {os.getenv('TELEGRAM_BOT_TOKEN')[:5]}...")
if 'OPENAI_API_KEY_JF' in os.environ:
    print(f"OpenAI key starts with: {os.getenv('OPENAI_API_KEY_JF')[:5]}...")

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY_JF')
openai_client = OpenAI(api_key=openai.api_key)

# Initialize database
if 'WEBSITE_SITE_NAME' in os.environ:  # Check if running on Azure
    database = "/home/site/wwwroot/telegram_chat.db"
else:
    database = "telegram_chat.db"

print(f"Using database at: {database}")
conn = create_connection(database)
create_table(conn)

# Bot configuration
messages_by_chat_id = {}
MAX_MESSAGES = 5
ai_model = "gpt-4"  # Changed to gpt-4 temporarily for testing
current_version = "DEBUG VERSION 1.0"

# Your existing prompt
main_prompt = """Your existing prompt here"""

print(f"Bot initialized with model: {ai_model}")

async def call_openai_api(api_model, command, conversation_history, max_tokens=None):
    try:
        print(f"Calling OpenAI API with model: {api_model}")
        print(f"Command: {command}")
        
        formatted_messages = [{"role": "system", "content": main_prompt}]
        formatted_messages.extend(conversation_history)
        
        print(f"Sending {len(formatted_messages)} messages to OpenAI")
        
        response = openai_client.chat.completions.create(
            model=api_model,
            messages=formatted_messages,
            max_tokens=max_tokens or 150,
            temperature=0.888,
            frequency_penalty=0.555,
            presence_penalty=0.666
        )
        
        print(f"Got response from OpenAI: {response.choices[0].message.content[:50]}...")
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        logger.error(f"OpenAI API error: {e}")
        raise

async def test_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to verify bot is working"""
    print("Test command received!")
    await update.message.reply_text("Bot is working!")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print(f"Reset command received from chat {update.message.chat.id}")
        chat_id = update.message.chat.id
        if chat_id in messages_by_chat_id:
            messages_by_chat_id[chat_id].clear()
        await context.bot.send_message(chat_id=chat_id, text="Context has been reset.")
    except Exception as e:
        print(f"Error in reset_command: {e}")
        logger.error(f"Error in reset_command: {e}")

async def current_version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("Version command received")
        chat_id = update.message.chat.id
        await context.bot.send_message(chat_id=chat_id, text=f"Current Version is: {current_version}")
    except Exception as e:
        print(f"Error in current_version_command: {e}")
        logger.error(f"Error in current_version_command: {e}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Message received from chat {update.message.chat.id}")
    chat_id = update.message.chat.id

    if chat_id not in messages_by_chat_id:
        messages_by_chat_id[chat_id] = []

    chat_messages = messages_by_chat_id[chat_id]

    if update.message:
        try:
            current_datetime = update.message.date
            user_full_name = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()
            user_message_text = update.message.text

            print(f"Processing message: {user_message_text[:50]}...")

            formatted_user_message = {'role': 'user', 'content': f"{user_full_name}: {user_message_text}"}
            chat_messages.append(formatted_user_message)

            # Store message in database
            insert_message(conn, (user_full_name, current_datetime, user_message_text))

            if len(chat_messages) > MAX_MESSAGES:
                chat_messages = chat_messages[-MAX_MESSAGES:]
                messages_by_chat_id[chat_id] = chat_messages

            if re.search(r'fiji', user_message_text, re.IGNORECASE):
                try:
                    print("Fiji keyword found, calling OpenAI")
                    ai_response = await call_openai_api(
                        api_model=ai_model,
                        command=user_message_text,
                        conversation_history=chat_messages
                    )

                    formatted_ai_response = ai_response.replace('Fiji: ', '', 1).replace('\\n', ' ').replace('\n', ' ')
                    
                    assistant_message = {'role': 'assistant', 'content': f"Fiji: {formatted_ai_response}"}
                    chat_messages.append(assistant_message)
                    
                    print(f"Sending response: {formatted_ai_response[:50]}...")
                    
                    # Store bot response in database
                    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
                    insert_message(conn, ("Fiji", time_now, formatted_ai_response))
                    
                    await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)

                except Exception as e:
                    print(f"Error processing message: {e}")
                    logger.error(f"Error processing message: {e}")
                    await context.bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error processing your message.")

        except Exception as e:
            print(f"Error in chat handler: {e}")
            logger.error(f"Error in chat handler: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, something went wrong.")

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check command to verify all systems"""
    try:
        chat_id = update.message.chat.id
        status = {
            "bot_running": True,
            "openai_configured": bool(openai.api_key),
            "database_connected": bool(conn),
        }
        status_msg = "Bot Health Check:\n" + "\n".join(f"- {k}: {v}" for k, v in status.items())
        await context.bot.send_message(chat_id=chat_id, text=status_msg)
    except Exception as e:
        print(f"Error in health check: {e}")
        logger.error(f"Error in health check: {e}")

def main():
    print("Starting bot...")
    try:
        # Initialize the application
        application = ApplicationBuilder().token(
            os.getenv('TELEGRAM_BOT_TOKEN')
        ).build()

        # Add handlers
        print("Registering handlers...")
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
        application.add_handler(CommandHandler('fixfiji', reset_command))
        application.add_handler(CommandHandler('current_version', current_version_command))
        application.add_handler(CommandHandler('test', test_webhook))
        application.add_handler(CommandHandler('health', health_check))

        print("Starting polling...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"Critical error starting bot: {e}")
        logger.error(f"Critical error starting bot: {e}")
        raise

if __name__ == '__main__':
    print("Initializing bot...")
    while True:
        try:
            main()
        except Exception as e:
            print(f"Bot crashed: {e}")
            logger.error(f"Bot crashed: {e}")
            print("Restarting in 10 seconds...")
            time.sleep(10)