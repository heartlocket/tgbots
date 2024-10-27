import sys
import logging
import os
import asyncio
import re
from quart import Quart, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Set to DEBUG for detailed trace
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Initialize Quart app
app = Quart(__name__)
app.config["DEBUG"] = True  # Enable debug mode for Quart

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY_JF')
WEBHOOK_URL = os.getenv('WEBHOOK_URL').rstrip('/') if os.getenv('WEBHOOK_URL') else None

# Validate environment variables
if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    logger.error("Missing environment variables. Please set TELEGRAM_BOT_TOKEN, OPENAI_API_KEY_JF, and WEBHOOK_URL.")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
MAX_MESSAGES = 5
ai_model = "ft:gpt-4o-2024-08-06:personal::ALgc5rgE"
main_prompt = "Your main prompt content here"
messages_by_chat_id = {}

async def call_openai_api(api_model, conversation_history, max_tokens=None):
    try:
        logger.debug("Calling OpenAI API...")
        formatted_messages = [{"role": "system", "content": main_prompt}]
        formatted_messages.extend(conversation_history)
        response = client.chat.completions.create(
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

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user_message_text = update.message.text
    logger.info(f"Message received from {chat_id}: {user_message_text}")

    if chat_id not in messages_by_chat_id:
        messages_by_chat_id[chat_id] = []

    chat_messages = messages_by_chat_id[chat_id]
    chat_messages.append({'role': 'user', 'content': f"{update.message.from_user.full_name}: {user_message_text}"})
    if len(chat_messages) > MAX_MESSAGES:
        chat_messages = chat_messages[-MAX_MESSAGES:]
        messages_by_chat_id[chat_id] = chat_messages

    if re.search(r'(hitler|bot_name)', user_message_text, re.IGNORECASE):
        logger.debug("Trigger word detected, calling OpenAI...")
        ai_response = await call_openai_api(ai_model, chat_messages)
        await context.bot.send_message(chat_id=chat_id, text=ai_response)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Trigger not detected.")

# Handlers
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

@app.before_serving
async def startup():
    await application.initialize()
    await application.start()
    logger.info("Application initialized and started.")

@app.after_serving
async def shutdown():
    await application.stop()
    await application.shutdown()
    logger.info("Application stopped and shutdown.")

@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Webhook called")
    try:
        request_data = await request.get_json()
        logger.debug(f"Webhook data received: {request_data}")
        update = Update.de_json(request_data, application.bot)
        await application.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

# Main app runner
async def main():
    logger.info("Starting Quart application")
    await app.run_task(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

if __name__ == '__main__':
    asyncio.run(main())
