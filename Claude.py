import sys
import logging
import os
import asyncio
import anthropic
import re
from hypercorn.config import Config
from quart import Quart, request
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Initialize Quart app with specific config
app = Quart(__name__)
app.config["DEBUG"] = True
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max-body-size
app.config["RESPONSE_TIMEOUT"] = 300  # 5 minutes

# Create Hypercorn config
config = Config()
config.bind = ["0.0.0.0:8443"]
config.worker_class = "asyncio"
config.keep_alive_timeout = 75
config.use_reloader = True
config.accesslog = "-"

# Load environment variables
load_dotenv()

START_TIME = datetime.now()
TELEGRAM_BOT_TOKEN = os.getenv('JFCLAUDEBOT')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_LOCAL', '').rstrip('/')

# Validate environment variables
if not all([TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, WEBHOOK_URL]):
    logger.error("Missing environment variables. Please set TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, and WEBHOOK_LOCAL.")
    sys.exit(1)

application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
MAX_MESSAGES = 25

# Load system prompt
try:
    with open('claudeSystem.txt', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
except Exception as e:
    logger.error(f"Error reading System.txt: {e}")
    sys.exit(1)

# Initialize Anthropic client
client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

# Store conversation histories
conversations = {}

async def call_claude_api(chat_messages, max_tokens=None):
    logger.info("Calling Claude API...")
    try:
        # Convert the chat history format to Claude's expected format
        messages = []
        for msg in chat_messages:
            if msg['role'] == 'system':
                continue  # System message is handled separately
            content = msg['content']
            if msg['role'] == 'user':
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "assistant", "content": content})

        print(messages)
        def sync_claude_call():
            return client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens or 500,
                messages=messages,
                temperature=0.888
            )

        response = await asyncio.to_thread(sync_claude_call)
        return response.content[0].text

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return "Something went wrong with the AI response."

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_message = update.message.text
    user_name = update.message.from_user.full_name
    
    logger.info(f"Message received from {chat_id}: {user_message}")

    # Initialize conversation history if it doesn't exist
    if chat_id not in conversations:
        conversations[chat_id] = []

    # Add user message to conversation history
    conversations[chat_id].append({
        'role': 'user',
        'content': f"{user_name}: {user_message}"
    })

    # Maintain conversation history limit
    if len(conversations[chat_id]) > MAX_MESSAGES:
        conversations[chat_id] = conversations[chat_id][-MAX_MESSAGES:]

    # Check for trigger words (fiji or bot_name)
    if any(re.search(rf'\b{trigger}\b', user_message, re.IGNORECASE) for trigger in ['Claude', 'bot_name']):
        logger.debug("Trigger word detected, calling Claude...")
        
        # Get Claude's response
        claude_response = await call_claude_api(conversations[chat_id])
        
        # Clean up response (remove any "Claude: " prefix)
        cleaned_response = claude_response.replace('Claude: ', '')
        
        # Send response to Telegram
        await context.bot.send_message(chat_id=chat_id, text=cleaned_response)
        
        # Add Claude's response to conversation history
        conversations[chat_id].append({
            'role': 'assistant',
            'content': f"Claude: {cleaned_response}"
        })

        #print(conversations[chat_id])

# Add message handler
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

@app.before_serving
async def startup():
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

@app.after_serving
async def shutdown():
    await application.bot.delete_webhook()
    await application.stop()
    await application.shutdown()
    logger.info("Application stopped and shutdown.")

@app.route('/webhook', methods=['POST'])
async def webhook():
    received_time = datetime.now()
    try:
        json_data = await request.get_json(force=True, silent=True)
        telegram_message_time = datetime.fromtimestamp(json_data.get('message', {}).get('date', 0))
        
        logger.info(f"[{received_time}] Webhook received. Message sent at: {telegram_message_time}. "
                   f"Delay: {received_time - telegram_message_time}")
        
        if not json_data:
            logger.error("No JSON data received")
            return 'No JSON data received', 400

        asyncio.create_task(process_update_independently(json_data, received_time, telegram_message_time))
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

async def process_update_independently(json_data, received_time, sent_time):
    try:
        process_start_time = datetime.now()
        chat_id = json_data.get('message', {}).get('chat', {}).get('id', 'unknown')
        message_text = json_data.get('message', {}).get('text', 'no text')
        
        logger.info(f"Message Timeline:"
                   f"\n  Sent at:      {sent_time}"
                   f"\n  Received at:  {received_time}"
                   f"\n  Processing at:{process_start_time}"
                   f"\n  Total delay:  {process_start_time - sent_time}"
                   f"\n  Message:      '{message_text}' for chat {chat_id}")
        
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
        
        end_time = datetime.now()
        logger.info(f"Processing completed:"
                   f"\n  Total processing time: {end_time - process_start_time}"
                   f"\n  Total message lifecycle: {end_time - sent_time}")
    except Exception as e:
        logger.error(f"Error processing update independently: {e}")

async def main():
    logger.info("Starting Quart application")
    from hypercorn.asyncio import serve
    await serve(app, config)

if __name__ == '__main__':
    asyncio.run(main())