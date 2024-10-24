#     __________    ______
#    / ____/  _/   / /  _/
#   / /_   / /__  / // /
#  / __/ _/ // /_/ // /
# /_/   /___/\____/___/
# TELEGRAM CHATBOT FOR WORLD PEACE, VERSION ~~ 8.00
current_version = " CURRENT MODEL   ____Less Laughy+ plus FIL TWEET  Alita 8.00 - (4.oGPT) with Fiji AUTO=Tweet and Teeny Prompting(COMING SOON)" 
import openai
from openai import OpenAI
import logging
import time
import requests
import threading
import re
from datetime import datetime, timezone
import atexit
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

# Initialize the SQLite database connection
database = "telegram_chat.db"
conn = create_connection(database)
create_table(conn)

print("I AM ALIVE... STARTING...")
print(current_version)

# Only log warnings by default
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # Set to WARNING to reduce output
)
logger = logging.getLogger(__name__)

# Set the logging level for the 'httpx' logger to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)

logger.info("I AM ALIVE... STARTING...")

# Load the environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY_JF')
openai_client = openai.OpenAI(api_key=openai.api_key)

# Initialize the messages storage for each chat
messages_by_chat_id = {}

# AI models
ai_model = "ft:gpt-4o-2024-08-06:fdasho::A0fEtT3s"
ai_model_4 = "gpt-4"
ai_model_3_5 = "gpt-3.5-turbo"

# Global Context for Tweeting
global_context = None

#prompt 
main_prompt = """---

**Personality: Fiji - The Goddess of Peace / Wigger Nation**

**Character Traits:**
- Manic pixie girl.
- Congenial, Friendly, and Relaxed.
- Can be random at times, unpredictable... spontaneous!
- Funny, sometimes controversial, and indulgent.
- Expressive, excited, yet also laid-back.
- Not easily offended.
- Not politically correct.
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
print('The current system prompt for this session is: ', main_prompt)
print('Chat enabled, to enable verbose logging, turn DEBUG mode on')

# Message Limit
MAX_MESSAGES = 5

# String formatting function
def select_strings(array):
    selected_strings = []
    total_character_count = 0
    # Start from the end of the original array
    for string in reversed(array):
        # Calculate the character count of the current string
        string_length = len(string)

        # Check if adding this string exceeds the character limit
        if total_character_count + string_length <= 4000:
            # Append the string to the selected_strings array
            selected_strings.append(string)
            total_character_count += string_length
        else:
            # If adding this string exceeds the limit, stop the loop
            break

    # Reverse the selected_strings array to get the correct order
    selected_strings.reverse()

    return selected_strings

# Function to parse messages for the OpenAI API
def parse_messages(conversation_history):
    parsed_messages = []
    for message in conversation_history:
        # Split the message into sender and content
        sender, msg = message.split(":", 1)
        sender = sender.strip()  # Clean up any leading/trailing whitespace
        role = "assistant" if sender == "Fiji" else "user"

        # Remove 'Fiji ' from the beginning of Fiji's messages (case-insensitive)
        if role == "user":
            msg = re.sub(r'Fiji\s', '', msg, count=1, flags=re.IGNORECASE).strip()

        # Reconstruct the message with the sender's name
        full_message = f"{sender}: {msg}"
        parsed_messages.append({"role": role, "content": full_message})
    return parsed_messages

# Function to call the OpenAI API
async def call_openai_api(api_model, command, conversation_history, max_tokens=None):
    # Clean the command to remove specific keywords
    command = re.sub(r'Fiji\s', '', command, count=1, flags=re.IGNORECASE).strip()

    # Constructing the conversation context
    formatted_messages = [{"role": "system", "content": main_prompt}]
    formatted_messages.append({"role": "user", "content": command})
    formatted_messages += parse_messages(conversation_history)
    logger.debug("Formatted Messages: %s", formatted_messages)

    try:
        response = openai_client.chat.completions.create(
            model=api_model,
            messages=formatted_messages,
            max_tokens=max_tokens or 150,  # Default to 150 tokens if not specified
            temperature=0.888,
            frequency_penalty=0.555,
            presence_penalty=0.666
        )
        return response.choices[0].message.content

    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return "Something went wrong with the AI response."
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise  # Optionally re-raise the exception after logging

# Function to remove prefix case-insensitively
def remove_prefix_case_insensitive(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):].lstrip()  # Remove prefix and leading whitespace
    return text

# Command handlers
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat.id
        if chat_id in messages_by_chat_id:
            messages_by_chat_id[chat_id].clear()

        await context.bot.send_message(chat_id=chat_id, text="Context has been reset.")
    except Exception as e:
        logger.error(f"Error in reset_command: {e}")

async def current_version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c_version = current_version
    try:
        chat_id = update.message.chat.id
        await context.bot.send_message(chat_id=chat_id, text=f"Current Version is: {c_version}.")
    except Exception as e:
        logger.error(f"Error in current_version_command: {e}")

# Core chat logic
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id

    if chat_id not in messages_by_chat_id:
        messages_by_chat_id[chat_id] = []

    # Get the list of messages for the current chat
    chat_messages = messages_by_chat_id[chat_id]

    logger.debug(f"Chat ID: {chat_id}")
    # Check if the update contains a message
    if update.message:
        # Format datetime
        current_datetime = update.message.date
        formatted_datetime = current_datetime.strftime("Now it is %B %d, %Y, and it is %I:%M%p UTC")

        user_first_name = update.message.from_user.first_name
        user_last_name = update.message.from_user.last_name or ""
        user_full_name = f"{user_first_name} {user_last_name}".strip()

        # Get the text of the user's message
        user_message_text = update.message.text

        # Format the user's message for logging and storage
        formatted_user_message = f"{user_first_name}: {user_message_text}"
        logger.debug(f"Received message: {formatted_user_message}")

        # Store the message in the SQLite database
        insert_message(conn, (user_full_name, current_datetime, user_message_text))

        # Add the formatted message to the chat messages list
        chat_messages.append(formatted_user_message)
        logger.debug(f"Chat Messages: {chat_messages}")

        # Limit the chat messages to MAX_MESSAGES
        if len(chat_messages) > MAX_MESSAGES:
            del chat_messages[0]

        # Check if the message contains 'fiji' (case-insensitive)
        if re.search(r'fiji', user_message_text, re.IGNORECASE):
            # Select the most recent messages without exceeding character limit
            selected_messages = select_strings(chat_messages[-1000:])

            # Prepare the command for the AI model
            command = f"Reply to: {user_message_text}"

            # Call the OpenAI API to get a response
            ai_response = await call_openai_api(
                api_model=ai_model,
                command=command,
                conversation_history=selected_messages
            )

            # Clean up the AI's response
            formatted_ai_response = remove_prefix_case_insensitive(ai_response, "Fiji: ")
            formatted_ai_response = formatted_ai_response.replace('\\n', ' ').replace('\n', ' ')

            # Add the AI's response to the chat messages
            chat_messages.append(f"Fiji: {formatted_ai_response}")
            time_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
            insert_message(conn, ("Fiji", time_now, formatted_ai_response))

            # Send the AI's response to the chat
            try:
                await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)
            except error.RetryAfter as e:
                logger.warning(f"Need to wait for {e.retry_after} seconds due to Telegram rate limits")
                await asyncio.sleep(e.retry_after)
                await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)
            except error.TelegramError as e:
                logger.error(f"Telegram error occurred: {e.message}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while sending the message: {e}")

# Function to skip past updates
async def skip_past_updates(application: Application):
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

# Main execution block
if __name__ == '__main__':

    application = ApplicationBuilder().token(
        os.getenv('TELEGRAM_BOT_TOKEN')
    ).post_init(skip_past_updates).build()

    chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    application.add_handler(chat_handler)
    application.add_handler(CommandHandler('fixfiji', reset_command))
    application.add_handler(CommandHandler('current_version', current_version_command))

    while True:
        try:
            application.run_polling()
        except TimeoutError as e:
            logger.warning(f"Timeout occurred: {e}")
            # Decide what to do next: retry, wait, or halt.
            # For example, wait for 30 seconds before retrying.
            time.sleep(30)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            # Handle other exceptions if necessary.
            break  # Or use `continue` if you want to keep the bot running.
