import sys
import logging
import os
import asyncio
import re
from datetime import datetime, timezone

from quart import Quart, request
from dotenv import load_dotenv
from telegram import Update, error
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
import openai
from db_handler import create_connection, create_table, insert_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info("Application starting...")

# Initialize Quart
app = Quart(__name__)
PORT = int(os.environ.get('PORT', '8443'))  # Use port 8443 for HTTPS

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY_JF')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Public URL for Telegram to send updates

# Verify environment variables
if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    logger.error("Missing environment variables. Please set TELEGRAM_BOT_TOKEN, OPENAI_API_KEY_JF, and WEBHOOK_URL.")
    sys.exit(1)

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize database
database = "telegram_chat.db"
conn = create_connection(database)
create_table(conn)

# Bot configuration
current_version = "CURRENT MODEL: Version 8.00 with Fiji AUTO=Tweet"
messages_by_chat_id = {}
MAX_MESSAGES = 5
ai_model = "gpt-4"

main_prompt = """Your original prompt here"""

# Declare application and bot as global variables
application = None
bot = None

# Helper Functions

def remove_prefix_case_insensitive(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):].lstrip()
    return text

# OpenAI API call function
async def call_openai_api(api_model, conversation_history, max_tokens=None):
    try:
        formatted_messages = [{"role": "system", "content": main_prompt}]
        formatted_messages.extend(conversation_history)

        response = await openai.ChatCompletion.acreate(
            model=api_model,
            messages=formatted_messages,
            max_tokens=max_tokens or 150,
            temperature=0.888,
            frequency_penalty=0.555,
            presence_penalty=0.666
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Something went wrong with the AI response."

# Telegram Bot Handlers

async def test_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working!")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    messages_by_chat_id.pop(chat_id, None)
    await context.bot.send_message(chat_id=chat_id, text="Context has been reset.")

async def current_version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    await context.bot.send_message(chat_id=chat_id, text=f"Current Version is: {current_version}")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id

    if chat_id not in messages_by_chat_id:
        messages_by_chat_id[chat_id] = []

    chat_messages = messages_by_chat_id[chat_id]

    if update.message:
        current_datetime = update.message.date
        user_full_name = update.message.from_user.full_name
        user_message_text = update.message.text

        formatted_user_message = {'role': 'user', 'content': f"{user_full_name}: {user_message_text}"}

        insert_message(conn, (user_full_name, current_datetime, user_message_text))
        chat_messages.append(formatted_user_message)
        
        if len(chat_messages) > MAX_MESSAGES:
            chat_messages = chat_messages[-MAX_MESSAGES:]
            messages_by_chat_id[chat_id] = chat_messages

        if re.search(r'fiji', user_message_text, re.IGNORECASE):
            try:
                ai_response = await call_openai_api(
                    api_model=ai_model,
                    conversation_history=chat_messages
                )

                formatted_ai_response = remove_prefix_case_insensitive(ai_response, "Fiji: ")
                formatted_ai_response = formatted_ai_response.replace('\\n', ' ').replace('\n', ' ')

                assistant_message = {'role': 'assistant', 'content': f"Fiji: {formatted_ai_response}"}
                chat_messages.append(assistant_message)
                
                time_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
                insert_message(conn, ("Fiji", time_now, formatted_ai_response))
                
                await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)

            except error.RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await context.bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error.")

# Quart route to receive updates from Telegram
@app.route('/webhook', methods=['POST'])
async def webhook():
    global application  # Ensure we're using the global application variable
    request_data = await request.get_json()
    update = Update.de_json(request_data, bot)
    await application.process_update(update)
    return 'OK'

# Quart route to set the webhook
@app.route('/set_webhook', methods=['GET', 'POST'])
async def set_webhook():
    s = await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    if s:
        return "Webhook setup successful"
    else:
        return "Webhook setup failed"

@app.route('/health')
async def health():
    return 'OK'

async def main():
    global application  # Declare as global to modify the global variable
    global bot          # Declare as global to modify the global variable

    # Create application with proper configuration
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.add_handler(CommandHandler('test', test_webhook))
    application.add_handler(CommandHandler('fixfiji', reset_command))
    application.add_handler(CommandHandler('current_version', current_version_command))

    # Get the bot instance
    bot = application.bot

    # Delete any existing webhook and set a new one
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    # Initialize and start the application
    await application.initialize()
    await application.start()

    # Start the Quart app
    try:
        await app.run_task(host='0.0.0.0', port=PORT)
    finally:
        # Gracefully stop the application
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
