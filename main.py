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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import atexit
import telegram
from telegram import Update
from telegram import error
from telegram import Sticker
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters, ContextTypes, CommandHandler
from telegram.ext import filters
from telegram.ext import CallbackContext
from telegram.ext import PicklePersistence
from telegram import Bot
from telegram.error import TimedOut
import logging
import asyncio
import os
from dotenv import load_dotenv
import random
import string
import getpass
from db_handler import create_connection, create_table, insert_message
# Initialize the SQLite database connection
database = "telegram_chat.db"
conn = create_connection(database)
create_table(conn)


# Set up logging at the top of your script
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                   level=logging.INFO)
#logger = logging.getLogger(__name__)

# Then use logger.info, logger.warning, etc., to log messages throughout your code
#logger.info('Starting bot 2.0...')

print("I AM ALIVE... STARTING...")

# Load the environment variables
load_dotenv() 
openai.api_key = os.getenv('OPENAI_API_KEY_JF')
openai_client = openai.OpenAI(api_key=openai.api_key)
bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))

#update script
async def skip_past_updates(bot):
    print("Checking for past updates...")
    while True:
        updates = await bot.get_updates()
        if not updates:  # If no updates are found, break out of the loop.
            break
        print(f"Found {len(updates)} past updates.")
        last_update_id = updates[-1].update_id
        print(f"Setting offset to {last_update_id + 1}")
        await bot.get_updates(offset=last_update_id + 1)
    print("No more past updates found.")

# Manually create and run the event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(skip_past_updates(bot))

#import shutdown callback
async def shutdown_callback(application):
    print("Shutting down bot...")
    await application.shutdown()
    # Perform any additional cleanup here if necessary

# I dont know what this does
executor = ThreadPoolExecutor(max_workers=1)

# Initialize variables Chat ID Stacks
group_conversations = {}
message_stacks = {}
chat_contexts = {}

# Chat ID context stacks for Dm's and Groups
group_conversation = []
message_stack = []

#mid cute
ai_model = "ft:gpt-4o-2024-08-06:fdasho::A0fEtT3s"
ai_model_4= "gpt-4"
ai_model_3_5 = "gpt-3.5-turbo"
global_chat_id = -1001898328325

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

# Message Limit
MAX_MESSAGES = 1000

# Pickle Persistence for Logging Updates and Prevents Spam Overflow
pp = PicklePersistence(filepath='my_persistence', single_file=False, on_flush=True)

#string formatting
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

# function for posting stickers
def sticker_handler(update: Update, context: CallbackContext):
    if update.message and update.message.sticker:
        sticker_file_id = update.message.sticker.file_id
        print(f"Received sticker with file_id: {sticker_file_id}")

#format message for user / assistant API calls 
def parse_messages(message_stack):
    parsed_messages = []
    for message in message_stack:
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


async def call_openai_api(api_model, command, larger_context, max_tokens=None):
    # Clean the command to remove specific keywords
    command = re.sub(r'Fiji\s', '', command, count=1, flags=re.IGNORECASE).strip()

    # Constructing the conversation context
    context_messages = [{"role": "system", "content": main_prompt}]
    context_messages.append({"role": "user", "content": command})
    context_messages += parse_messages(larger_context)
    print("context", context_messages)

    print(context_messages)  # Debugging: Print context messages
    try:
        response = openai_client.chat.completions.create(
            model=api_model,
            messages=context_messages,
            max_tokens=max_tokens or 150,  # Default to 150 tokens if not specified
            temperature=0.888,
            frequency_penalty=0.555,
            presence_penalty=0.666
        )
        return response.choices[0].message.content

    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return "Something went wrong with the AI response."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise  # Optionally re-raise the exception after logging

#fixfiji context reset
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Increment the counter each time the reset command is called

        chat_id = update.message.chat.id
        if chat_id in message_stacks:
            message_stacks[chat_id].clear()
            group_conversations[chat_id].clear()

        await context.bot.send_message(chat_id=chat_id, text=f"Context has been reset. Command called {count} times.")
    except Exception as e:
        print(f"Error in reset_command: {e}")

#announce current dev version name
async def current_version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c_version = current_version
    try:
        # Increment the counter each time the reset command is called
        chat_id = update.message.chat.id
        await context.bot.send_message(chat_id=chat_id, text=f"Current Version is : {c_version}.")
    except Exception as e:
        print(f"Error in reset_command: {e}")

#funciton to remove 'fiji' from beginning of string
def remove_prefix_case_insensitive(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):].lstrip()  # Remove prefix and leading whitespace
    return text

#core chat logic
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_context
    chat_id = update.message.chat.id

    if chat_id == global_chat_id:
        global_context = context

    if chat_id not in message_stacks:
          message_stacks[chat_id] = []
          group_conversations[chat_id] = []

    # Create local references to the specific chat's stacks
    message_stack = message_stacks[chat_id]
    group_conversation = group_conversations[chat_id]

    print(f"Chat ID: {chat_id}")
    # check if update is a message
    if update.message:

        # format datetime
        current_datetime = update.message.date
        tempdate = current_datetime.strftime("%H:%M:%S")
        custom_format = "Now it is %B %d, %Y, and it is %I:%M%p UTC"
        formatted_datetime = current_datetime.strftime(custom_format)

        first_name = update.message.from_user.first_name
        last_name = update.message.from_user.last_name 
        full_name = f"{first_name} {last_name}"

        # Extract the user's first name and the message text
        user_name = update.message.from_user.first_name
        message_text = update.message.text
        
        formatted_message = f"{user_name}: {message_text}"
        #print(f"{formatted_message}\n\n")

        # Store the message in the SQLite database
        insert_message(conn, (full_name, current_datetime, message_text))

        # Add the formatted message to the stacks
        message_stack.append(formatted_message)
        group_conversation.append(formatted_message)
        print(f"Message Stack: {message_stack}")

        if len(group_conversation) > MAX_MESSAGES:
            del group_conversation[0]

        if re.search(r'fiji', message_text, re.IGNORECASE):

            # select most recent strings from general conversation list, need to consider number
            general_conversation = select_strings(group_conversation[-3050:])

             # select most recent strings from general conversation list, need to consider number
            shorter_stack = select_strings(group_conversation[-999:])

            conversation_str_message = "\n".join(message_stack)  # gpt read for message
            conversation_str_shorter = "\n".join(shorter_stack)  # gpt for shorter context
            conversation_str_group = "\n".join(general_conversation)  # gpt for larger context

            #print(conversation_str_message)
            #print(conversation_str_shorter)
            #print(conversation_str_group)

            # probably cleaner way to mandate response if sentence begins with FIJI
            should_reply = True
            command = f"""reply to : {update.message.text}"""
            response = await call_openai_api(ai_model, command=command, larger_context=shorter_stack)

            # formulate comment with API call with past context and current comments
                
            try:
                
                # add new response to group conversation list
                print(f"Original Response: {response}")

                formatted_response = remove_prefix_case_insensitive(response, "Fiji: ")
                print(f"Fiji Formatted : {formatted_response}")

                formatted_response = formatted_response.replace('\\n', ' ')  # For escaped newline
                formatted_response = formatted_response.replace('\n', ' ')   # For regular newline

                print(f"After replacement: {formatted_response}")

                group_conversation.append(f"Fiji: {formatted_response}")
                time_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
                insert_message(conn, ("Fiji", time_now, formatted_response))

                #conversation_strNEW = "\n".join(group_conversation[-50:])
                #print(f"Recent General Convo\n\n: {conversation_strNEW}")

                # send message to channel
                await context.bot.send_message(chat_id=update.message.chat.id, text=formatted_response)

                # Sticker file --- is this too big?
                #your_sticker_file_id = "CAACAgEAAxkBAAEnAsJlNHEpaCLrB6VsS6IWzdw7Rp5ybQAC0AMAAvBWQEWhveTp-VuiDTAE"
                #await context.bot.send_sticker(chat_id=update.message.chat.id, sticker=your_sticker_file_id)

            except error.RetryAfter as e:
                
                # If we get a RetryAfter error, we wait for the specified time and then retry

                print(f"Need to wait for {e.retry_after} seconds due to Telegram rate limits")

                await asyncio.sleep(e.retry_after)

                # Retry sending the message and sticker after waiting

                await context.bot.send_message(chat_id=update.message.chat.id, text=formatted_response)
                await context.bot.send_sticker(chat_id=update.message.chat.id, sticker=your_sticker_file_id)

            except error.TelegramError as e:
                
                # Handle other Telegram related errors
                print(f"Telegram error occurred: {e.message}")
            except Exception as e:
                
                # Handle any other exceptions
                print(f"An unexpected error occurred while sending the message or sticker: {e}")
    pass

#init
if __name__ == '__main__':

    application = ApplicationBuilder().token(
        os.getenv('TELEGRAM_BOT_TOKEN')
    ).build()

    chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    application.add_handler(chat_handler)
    application.add_handler(CommandHandler('fixfiji', reset_command))
    application.add_handler(CommandHandler('current_version', current_version_command))

    # Register the shutdown callback
    atexit.register(shutdown_callback, application)
    
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
