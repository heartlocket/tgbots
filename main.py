import sys
import logging
import os
import asyncio
from asyncio import Semaphore
from collections import defaultdict, deque
import re
from typing import Set
import time
from quart import Quart, request
from hypercorn.config import Config
from hypercorn.asyncio import serve
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)
import openai
from openai import OpenAI

# Load environment variables
load_dotenv(override=True)

print("IM IN AZURE... BOT")
# Import WalletRanker
from wallet_ranker import WalletRanker

# Initialize WalletRanker and semaphores
wallet_ranker = WalletRanker()
quant_semaphores = defaultdict(lambda: Semaphore(1))



# Initialize Quart app
app = Quart(__name__)
app.config["DEBUG"] = True
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max-body-size
app.config["RESPONSE_TIMEOUT"] = 300  # 5 minutes

# Task Background for Clean Shutdowns
background_tasks: Set[asyncio.Task] = set()

def register_background_task(task: asyncio.Task) -> None:
    """Register a background task for cleanup."""
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


# Create Hypercorn config
config = Config()
config.bind = ["0.0.0.0:8000"]
config.worker_class = "asyncio"
config.keep_alive_timeout = 75
config.use_reloader = False  # Set to False in production
config.accesslog = "-"

print(f"PORT: {os.getenv('PORT', '8000')}")
print("Starting server on port 8000...")
sys.stdout.flush()  # Force the print to show up in logs

START_TIME = datetime.now()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add these debug lines at the start of your main.py
logger.info(f"Starting bot...")
logger.info(f"WEBHOOK_URL: {os.getenv('WEBHOOK_URL')}")
logger.info(f"Bot Token available: {'yes' if os.getenv('TELEGRAM_BOT_TOKEN') else 'no'}")
logger.info(f"OpenAI Key available: {'yes' if os.getenv('OPENAI_API_KEY') else 'no'}")

# Load environment variables

WEBHOOK_URL = os.getenv('WEBHOOK_URL').rstrip('/') if os.getenv('WEBHOOK_URL') else None
logger.info(f"WEBHOOK_URL is set to: {WEBHOOK_URL}")


if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    logger.error("Missing environment variables.")
    sys.exit(1)

# Initialize OpenAI and Telegram application
client = OpenAI(api_key=OPENAI_API_KEY)
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).updater(None).build()
MAX_MESSAGES = 25

ai_model = "ft:gpt-4o-2024-08-06:fdasho::A0fEtT3s"

# Load system prompt
try:
    with open('fijiSystem.txt', 'r', encoding='utf-8') as file:
        fiji_system = file.read()
except Exception as e:
    logger.error(f"Error reading fijiSystem.txt: {e}")
    sys.exit(1)

main_prompt = fiji_system

# Store messages per chat
messages_by_chat_id = defaultdict(lambda: deque(maxlen=MAX_MESSAGES))

async def call_openai_api(api_model, conversation_history, max_tokens=None):
    logger.info("Calling OpenAI API...")
    try:
        formatted_messages = [{"role": "system", "content": main_prompt}]
        formatted_messages.extend(conversation_history)
        
        def sync_openai_call():
            return client.chat.completions.create(
                model=api_model,
                messages=formatted_messages,
                max_tokens=max_tokens or 500,
                temperature=0.888,
                frequency_penalty=0.555,
                presence_penalty=0.666,
            )
        
        response = await asyncio.to_thread(sync_openai_call)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Something went wrong with the AI response."

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_message_text = update.message.text
    logger.info(f"Message received from {chat_id}: {user_message_text}")

    chat_messages = messages_by_chat_id[chat_id]
    chat_messages.append({'role': 'user', 'content': f"{update.message.from_user.full_name}: {user_message_text}"})
    
    if re.search(r'(fiji|bot_name)', user_message_text, re.IGNORECASE):
        logger.debug("Trigger word detected, calling OpenAI...")
        ai_response = await call_openai_api(ai_model, list(chat_messages))
        cleaned_response = ai_response.replace('FIJI: ', '')
        await context.bot.send_message(chat_id=chat_id, text=cleaned_response)
        chat_messages.append({'role': 'assistant', 'content': f"FIJI: {cleaned_response}"})

async def quant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if not quant_semaphores[chat_id].locked():
        async with quant_semaphores[chat_id]:
            try:
                if not context.args:
                    await update.message.reply_text("Please provide a wallet address. Usage: /QUANT [wallet_address]")
                    return

                wallet_address = context.args[0]
                processing_message = await update.message.reply_text("Analyzing wallet... 🔍")

                try:
                    ranker = WalletRanker()
                    analysis_result = await ranker.analyze_wallet(wallet_address)

                    if analysis_result:
                        await context.bot.send_message(
                          chat_id=chat_id, 
                          text=analysis_result,
                          parse_mode='HTML'
                      )
                    else:
                        await update.message.reply_text("No data found for this wallet or analysis failed.")
                finally:
                    try:
                        await processing_message.delete()
                    except Exception as e:
                        logger.error(f"Failed to delete processing message: {e}")
            except Exception as e:
                logger.error(f"Error in quant_command for chat {chat_id}: {e}")
                await update.message.reply_text(f"Error analyzing wallet: {str(e)}")
    else:
        await update.message.reply_text("A wallet analysis is already in progress in this chat. Please wait.")




application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
application.add_handler(CommandHandler("QUANT", quant_command))



# Telegram Webook and Quart app setup
@app.before_serving
async def startup():
    try:
        await application.initialize()
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=["message"],
            max_connections=100,
            read_timeout=60
        )
        await application.start()
        logger.info("Application initialized and started.")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.after_serving
async def shutdown():
    try:
        # Cancel all background tasks first
        if background_tasks:
            logger.info(f"Cancelling {len(background_tasks)} background tasks")
            for task in background_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*background_tasks, return_exceptions=True)
            background_tasks.clear()
        
        # Delete webhook
        try:
            await application.bot.delete_webhook()
            logger.info("Webhook deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
        
        # Signal update fetcher to stop
        try:
            # Use try_put_nowait to avoid blocking if queue is full
            try:
                application.update_queue.put_nowait(None)
                logger.info("Update fetcher signaled to stop")
            except asyncio.QueueFull:
                logger.warning("Could not signal update fetcher - queue full")
        except Exception as e:
            logger.error(f"Error signaling update fetcher: {e}")
        
        # Stop the application
        if hasattr(application, 'running') and application.running:
            try:
                await application.stop()
                logger.info("Application stopped")
            except Exception as e:
                logger.error(f"Error stopping application: {e}")
        
        # Final shutdown
        try:
            await application.shutdown()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    except Exception as e:
        logger.error(f"Critical error during shutdown sequence: {e}")
    finally:
        logger.info("Shutdown sequence completed")

@app.route('/')
async def health_check():
    return {"status": "alive", "time": str(datetime.now())}

@app.route('/webhook', methods=['POST'])
async def webhook():
    start_time = time.perf_counter()
    request_id = generate_request_id()  # You'll need to implement this
    
    try:
        json_data = await request.get_json(force=True, silent=True)
        if not json_data:
            logger.error(f"[Request-ID: {request_id}] No JSON data received")
            return 'No JSON data received', 400

        telegram_message_time = datetime.fromtimestamp(json_data.get('message', {}).get('date', 0))
        logger.info(f"[Request-ID: {request_id}] Webhook received, message timestamp: {telegram_message_time}")
        
        # Use the current loop
        loop = asyncio.get_running_loop()
        task = loop.create_task(process_update_independently(json_data, request_id, start_time))
        register_background_task(task)
        
        handler_duration = time.perf_counter() - start_time
        logger.info(f"[Request-ID: {request_id}] Webhook handler completed in {handler_duration:.3f}s")
        return 'OK', 200
    except Exception as e:
        handler_duration = time.perf_counter() - start_time
        logger.error(f"[Request-ID: {request_id}] Webhook error: {e}, duration: {handler_duration:.3f}s")
        return 'Error', 500

async def process_update_independently(json_data, request_id, start_time):
    process_start_time = time.perf_counter()
    try:
        update = Update.de_json(json_data, application.bot)
        # Log before processing
        logger.info(f"[Request-ID: {request_id}] Starting update processing at {process_start_time - start_time:.3f}s from webhook start")
        
        # Ensure we're using the same loop as the application
        await asyncio.get_running_loop().create_task(
            application.process_update(update)
        )
        
        process_duration = time.perf_counter() - process_start_time
        total_duration = time.perf_counter() - start_time
        logger.info(
            f"[Request-ID: {request_id}] Update processing completed:\n"
            f"  Processing time: {process_duration:.3f}s\n"
            f"  Total time from webhook start: {total_duration:.3f}s"
        )
    except Exception as e:
        process_duration = time.perf_counter() - process_start_time
        total_duration = time.perf_counter() - start_time
        logger.error(
            f"[Request-ID: {request_id}] Error processing update:\n"
            f"  Error: {e}\n"
            f"  Processing time: {process_duration:.3f}s\n"
            f"  Total time from webhook start: {total_duration:.3f}s"
        )
    finally:
        current_task = asyncio.current_task()
        if current_task and current_task in background_tasks:
            background_tasks.discard(current_task)

def generate_request_id():
    """Generate a unique request ID for tracking purposes"""
    return f"req-{int(time.time() * 1000)}-{id(time)}"

async def main():
    logger.info("Starting Quart application")
    try:
        await serve(app, config)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        # Ensure cleanup happens even if serve fails
        if background_tasks:
            logger.info("Cleaning up remaining background tasks")
            for task in background_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*background_tasks, return_exceptions=True)

if __name__ == '__main__':
    asyncio.run(main())