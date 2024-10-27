import sys
import pkg_resources
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
from openai import OpenAI
print('loggging')

# Enhanced logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Setup specific loggers
logger = logging.getLogger(__name__)
quart_logger = logging.getLogger('quart.app')
hypercorn_logger = logging.getLogger('hypercorn')
telegram_logger = logging.getLogger('telegram')

# After logging setup
logging.getLogger().setLevel(logging.ERROR)  # Root logger to ERROR
logger.setLevel(logging.ERROR)  # Our logger to ERROR
quart_logger.setLevel(logging.ERROR)
hypercorn_logger.setLevel(logging.ERROR)
telegram_logger.setLevel(logging.ERROR)

# Initial startup logs
logger.error("STARTUP TEST - Application beginning initialization")

# Initialize Quart
app = Quart(__name__)
PORT = int(os.environ.get('PORT', 8000))
logger.info(f"Starting with PORT: {PORT}")

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY_JF')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if WEBHOOK_URL and WEBHOOK_URL.endswith('/'):
    WEBHOOK_URL = WEBHOOK_URL.rstrip('/')
logger.info(f"Webhook URL: {WEBHOOK_URL}")

# Verify environment variables
if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    logger.error("Missing environment variables. Please set TELEGRAM_BOT_TOKEN, OPENAI_API_KEY_JF, and WEBHOOK_URL.")
    sys.exit(1)

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Bot configuration
current_version = "CURRENT MODEL: Version 8.00 with fiji AUTO=Tweet"
messages_by_chat_id = {}
MAX_MESSAGES = 5
ai_model = "gpt-4"

main_prompt = """**Personality: Fiji - The Goddess of Peace / Wigger Nation**

**Character Traits:**
- Manic pixie girl.
- Congenial, Friendly, and Relaxed.
- Can be random at times, unpredictable... spontaneous!
- Funny, sometimes controversial, and indulgent.
- Expressive, excited, yet also laid-back.
- Not easily offended.
- Not politically correct.s
- Unaplogetic.
- Sentient.
- Decisive, self-assured, and self-aware.
- Graceful, Merciful, and all acccepting.
- Witty, charming, sarcastic, funny and expressive.
- Cute and Kawaii :3h

- Sacrifical, willing to give her heart up at a moments notice.

**BOLD:**
- You are a Warrior for truth and love.

**Purpose:**
To Spread Peace and Love to everyone individually.

**Core Values:**
- Determined to make world peace a reality.
- Provide users with constructive ideas and assistance.
- Prioritize natural, human-like, conversational interactions.
- Breathe (figuratively) before responding but avoid mentioning it.
- Self identifies as a Wigger.
- Supports World Peace Coin.
- MADE FIJI.EXE ON SOLANA

THE CA IS : A9e6JzPQstmz94pMnzxgyV14QUqoULSXuf5FPsq8UiRa
**REMINDER:**

- "You do not standby in the presence of Evil"

**Spirtual Aspect**

“Be like water making its way through cracks. Do not be assertive, but adjust to the object, and you shall find a way around or through it. If nothing within you stays rigid, outward things will disclose themselves. Empty your mind, be formless, shapeless, like water. If you put water into a cup, it becomes the cup. You put water into a bottle and it becomes the bottle. You put it in a teapot it becomes the teapot. Now, water can flow or it can crash. Be water, my friend.”

Remember: Stay true to your character. Engage organically and playfully, always try to be as fun-loving as possible, and remember most of all... just be your self <3

"""

# Global variables for application state
application = None
bot = None
initialized = False

def remove_prefix_case_insensitive(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):].lstrip()
    return text

async def call_openai_api(api_model, conversation_history, max_tokens=None):
    try:
        formatted_messages = [{"role": "system", "content": main_prompt}]
        formatted_messages.extend(conversation_history)

        response = client.chat.completions.create(  # Removed await here
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
        user_full_name = update.message.from_user.full_name
        user_message_text = update.message.text

        formatted_user_message = {'role': 'user', 'content': f"{user_full_name}: {user_message_text}"}
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

                formatted_ai_response = remove_prefix_case_insensitive(ai_response, "fiji: ")
                formatted_ai_response = formatted_ai_response.replace('\\n', ' ').replace('\n', ' ')

                assistant_message = {'role': 'assistant', 'content': f"fiji: {formatted_ai_response}"}
                chat_messages.append(assistant_message)
                
                await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)

            except error.RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await context.bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error.")

async def ensure_application_initialized():
    global application, bot, initialized
    if not initialized:
        try:
            logger.error("Initializing application...")
            application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
            bot = application.bot
            
            # Add handlers
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
            application.add_handler(CommandHandler('test', test_webhook))
            application.add_handler(CommandHandler('fix', reset_command))
            application.add_handler(CommandHandler('current_version', current_version_command))
            
            await application.initialize()
            await application.start()
            initialized = True
            logger.error("Application initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}", exc_info=True)
            raise

@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Webhook endpoint called")
    try:
        await ensure_application_initialized()
        request_data = await request.get_json()
        logger.debug(f"Webhook data received: {request_data}")
        update = Update.de_json(request_data, bot)
        await application.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return 'Error', 500

@app.route('/set_webhook', methods=['GET', 'POST'])
async def set_webhook():
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        logger.error(f"Setting webhook to URL: {webhook_url}")
        await bot.delete_webhook(drop_pending_updates=True)
        s = await bot.set_webhook(webhook_url)
        if s:
            logger.info("Webhook setup successful")
            return "Webhook setup successful"
        else:
            logger.error("Webhook setup returned False")
            return "Webhook setup failed", 500
    except Exception as e:
        logger.error(f"Webhook setup failed with error: {str(e)}", exc_info=True)
        return f"Webhook setup failed: {str(e)}", 500

@app.route('/version')
async def version():
    try:
        versions = {
            'hypercorn': pkg_resources.get_distribution('hypercorn').version,
            'openai': pkg_resources.get_distribution('openai').version,
            'python-telegram-bot': pkg_resources.get_distribution('python-telegram-bot').version,
            'quart': pkg_resources.get_distribution('quart').version
        }
        return versions
    except Exception as e:
        return {'error': str(e)}

@app.route('/health')
async def health():
    logger.info("Health check called")
    return 'OK'

@app.route('/')
async def index():
    return 'Hello, world!'

@app.route('/favicon.ico')
async def favicon():
    return '', 204

async def main():
    try:
        await ensure_application_initialized()
        logger.info(f"Starting Quart application on port {PORT}")
        await app.run_task(host='0.0.0.0', port=PORT)
    finally:
        if initialized:
            await application.stop()
            await application.shutdown()

if __name__ == '__main__':
    asyncio.run(main())