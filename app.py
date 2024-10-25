import sys
import logging
import os
import threading
import asyncio
import time
import re
from datetime import datetime, timezone

from flask import Flask
from dotenv import load_dotenv
from telegram import Update, error
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
    Application,
)

import openai
import requests  # If you're using it elsewhere
from db_handler import create_connection, create_table, insert_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/LogFiles/application.log')
    ]
)
logger = logging.getLogger(__name__)
logger.info("Application starting...")

# Initialize Flask
app = Flask(__name__)
PORT = os.getenv('PORT', '8000')

@app.route('/health')
def health():
    return 'OK'

try:
    # Load environment variables
    load_dotenv()
    logger.info("Environment variables loaded")
    logger.info(f"Bot token exists: {'TELEGRAM_BOT_TOKEN' in os.environ}")
    logger.info(f"OpenAI key exists: {'OPENAI_API_KEY_JF' in os.environ}")

    # Initialize OpenAI
    logger.info("Initializing OpenAI...")
    openai.api_key = os.getenv('OPENAI_API_KEY_JF')
    logger.info("OpenAI initialized")

    # Initialize database
    logger.info("Setting up database...")
    if 'WEBSITE_SITE_NAME' in os.environ:
        database = "/home/site/wwwroot/telegram_chat.db"
    else:
        database = "telegram_chat.db"
    logger.info(f"Database path: {database}")
    
    conn = create_connection(database)
    create_table(conn)
    logger.info("Database initialized")

    # Bot configuration
    current_version = "CURRENT MODEL: Less Laughy+ plus FIL TWEET Alita 8.00 - (GPT-4) with Fiji AUTO=Tweet and Teeny Prompting (COMING SOON)"
    messages_by_chat_id = {}
    MAX_MESSAGES = 5
    ai_model = "gpt-4"  # Update with your actual model if needed
    ai_model_3_5 = "gpt-3.5-turbo"
    logger.info("Bot configured")

    main_prompt = """Your original prompt here"""
    logger.info("Main prompt loaded")

    # Helper Functions

    def remove_prefix_case_insensitive(text, prefix):
        if text.lower().startswith(prefix.lower()):
            return text[len(prefix):].lstrip()
        return text

    # OpenAI API call function
    async def call_openai_api(api_model, conversation_history, max_tokens=None):
        logger.info("Calling OpenAI API")
        try:
            formatted_messages = [{"role": "system", "content": main_prompt}]
            formatted_messages.extend(conversation_history)
            
            logger.debug("Formatted Messages: %s", formatted_messages)

            response = openai.ChatCompletion.create(
                model=api_model,
                messages=formatted_messages,
                max_tokens=max_tokens or 150,
                temperature=0.888,
                frequency_penalty=0.555,
                presence_penalty=0.666
            )
            logger.info("OpenAI API call successful")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "Something went wrong with the AI response."

    # Telegram Bot Handlers

    async def test_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Test command received!")
        await update.message.reply_text("Bot is working!")

    async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat_id = update.message.chat.id
            messages_by_chat_id.pop(chat_id, None)
            await context.bot.send_message(chat_id=chat_id, text="Context has been reset.")
        except Exception as e:
            logger.error(f"Error in reset_command: {e}")

    async def current_version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat_id = update.message.chat.id
            await context.bot.send_message(chat_id=chat_id, text=f"Current Version is: {current_version}")
        except Exception as e:
            logger.error(f"Error in current_version_command: {e}")

    async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Chat function called")
        chat_id = update.message.chat.id

        if chat_id not in messages_by_chat_id:
            messages_by_chat_id[chat_id] = []

        chat_messages = messages_by_chat_id[chat_id]

        if update.message:
            try:
                current_datetime = update.message.date
                user_full_name = update.message.from_user.full_name
                user_message_text = update.message.text

                formatted_user_message = {'role': 'user', 'content': f"{user_full_name}: {user_message_text}"}
                logger.info(f"Received message: {user_message_text[:50]}...")

                insert_message(conn, (user_full_name, current_datetime, user_message_text))
                chat_messages.append(formatted_user_message)
                
                if len(chat_messages) > MAX_MESSAGES:
                    chat_messages = chat_messages[-MAX_MESSAGES:]
                    messages_by_chat_id[chat_id] = chat_messages

                if re.search(r'fiji', user_message_text, re.IGNORECASE):
                    logger.info("Fiji keyword found")
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
                        
                        logger.info("Sending response to user")
                        await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)

                    except error.RetryAfter as e:
                        logger.error(f"Rate limit error: {e}")
                        await asyncio.sleep(e.retry_after)
                        await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await context.bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error.")

            except Exception as e:
                logger.error(f"Error in chat handler: {e}")
                await context.bot.send_message(chat_id=chat_id, text="Sorry, something went wrong.")

    async def skip_past_updates(application: Application):
        logger.info("Skipping past updates")
        bot = application.bot
        logger.info("Checking for past updates...")
        while True:
            updates = await bot.get_updates()
            if not updates:
                break
            logger.info(f"Found {len(updates)} past updates.")
            last_update_id = updates[-1].update_id
            logger.info(f"Setting offset to {last_update_id + 1}")
            await bot.get_updates(offset=last_update_id + 1)
        logger.info("No more past updates found.")

    def run_bot():
        logger.info("Starting bot...")
        try:
            logger.info("Creating application builder...")
            application = ApplicationBuilder().token(
                os.getenv('TELEGRAM_BOT_TOKEN')
            ).post_init(skip_past_updates).build()
            logger.info("Application built")

            logger.info("Adding handlers...")
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
            application.add_handler(CommandHandler('test', test_webhook))
            application.add_handler(CommandHandler('fixfiji', reset_command))
            application.add_handler(CommandHandler('current_version', current_version_command))
            logger.info("Handlers added")

            logger.info("Starting polling...")
            application.run_polling(drop_pending_updates=True)
            logger.info("Polling started")

        except Exception as e:
            logger.error(f"Critical error starting bot: {e}")
            raise

    def main():
        logger.info("Starting main application...")
        # Start the bot in a separate thread
        bot_thread = threading.Thread(target=lambda: asyncio.run(run_bot()))
        bot_thread.daemon = True
        bot_thread.start()
        
        # Start the Flask application
        logger.info(f"Starting web server on port {PORT}")
        app.run(host='0.0.0.0', port=int(PORT))

    if __name__ == '__main__':
        while True:
            try:
                main()
            except Exception as e:
                logger.error(f"Application crashed: {e}")
                logger.info("Restarting in 10 seconds...")
                time.sleep(10)

except Exception as e:
    logger.error(f"Startup error: {e}")
    raise
