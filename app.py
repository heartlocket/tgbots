import sys
import logging
import os
from dotenv import load_dotenv

# Immediate startup logging
print("1. Script starting...", flush=True)
sys.stdout.flush()

# Configure logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/LogFiles/application.log')
    ]
)
logger = logging.getLogger(__name__)
print("2. Logging configured", flush=True)

try:
    # Load environment variables
    load_dotenv()
    print("3. Environment variables loaded", flush=True)
    print(f"4. Bot token exists: {'TELEGRAM_BOT_TOKEN' in os.environ}", flush=True)
    print(f"5. OpenAI key exists: {'OPENAI_API_KEY_JF' in os.environ}", flush=True)

    # Import other dependencies
    print("6. Importing dependencies...", flush=True)
    import openai
    from openai import OpenAI
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
    from db_handler import create_connection, create_table, insert_message
    print("7. All imports successful", flush=True)

    # Initialize OpenAI
    print("8. Initializing OpenAI...", flush=True)
    openai.api_key = os.getenv('OPENAI_API_KEY_JF')
    openai_client = OpenAI(api_key=openai.api_key)
    print("9. OpenAI initialized", flush=True)

    # Initialize database
    print("10. Setting up database...", flush=True)
    if 'WEBSITE_SITE_NAME' in os.environ:
        database = "/home/site/wwwroot/telegram_chat.db"
    else:
        database = "telegram_chat.db"
    print(f"11. Database path: {database}", flush=True)
    
    conn = create_connection(database)
    create_table(conn)
    print("12. Database initialized", flush=True)

    # Bot configuration
    current_version = " CURRENT MODEL   ____Less Laughy+ plus FIL TWEET  Alita 8.00 - (4.oGPT) with Fiji AUTO=Tweet and Teeny Prompting(COMING SOON)" 
    messages_by_chat_id = {}
    MAX_MESSAGES = 5
    ai_model = "ft:gpt-4o-2024-08-06:fdasho::A0fEtT3s"
    ai_model_4 = "gpt-4"
    ai_model_3_5 = "gpt-3.5-turbo"
    global_context = None
    print("13. Bot configured", flush=True)

    main_prompt = """Your original prompt here"""

    print("14. Main prompt loaded", flush=True)

    # Function to select strings
    def select_strings(array):
        selected_strings = []
        total_character_count = 0
        for string in reversed(array):
            string_length = len(string)
            if total_character_count + string_length <= 4000:
                selected_strings.append(string)
                total_character_count += string_length
            else:
                break
        selected_strings.reverse()
        return selected_strings

    def parse_messages(conversation_history):
        parsed_messages = []
        for message in conversation_history:
            role = message.get('role')
            msg = message.get('content')
            if role and msg:
                parsed_messages.append({"role": role, "content": msg})
        return parsed_messages

    async def call_openai_api(api_model, command, conversation_history, max_tokens=None):
        print("15. Calling OpenAI API", flush=True)
        try:
            formatted_messages = [{"role": "system", "content": main_prompt}]
            formatted_messages.extend(conversation_history)
            
            logger.debug("Formatted Messages: %s", formatted_messages)

            response = openai_client.chat.completions.create(
                model=api_model,
                messages=formatted_messages,
                max_tokens=max_tokens or 150,
                temperature=0.888,
                frequency_penalty=0.555,
                presence_penalty=0.666
            )
            print("16. OpenAI API call successful", flush=True)
            return response.choices[0].message.content

        except Exception as e:
            print(f"ERROR in OpenAI call: {str(e)}", flush=True)
            logger.error(f"OpenAI API error: {e}")
            return "Something went wrong with the AI response."

    def remove_prefix_case_insensitive(text, prefix):
        if text.lower().startswith(prefix.lower()):
            return text[len(prefix):].lstrip()
        return text

    async def test_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("Test command received!", flush=True)
        await update.message.reply_text("Bot is working!")

    async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat_id = update.message.chat.id
            if chat_id in messages_by_chat_id:
                messages_by_chat_id[chat_id].clear()
            await context.bot.send_message(chat_id=chat_id, text="Context has been reset.")
        except Exception as e:
            print(f"Error in reset_command: {str(e)}", flush=True)
            logger.error(f"Error in reset_command: {e}")

    async def current_version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat_id = update.message.chat.id
            await context.bot.send_message(chat_id=chat_id, text=f"Current Version is: {current_version}")
        except Exception as e:
            print(f"Error in current_version_command: {str(e)}", flush=True)
            logger.error(f"Error in current_version_command: {e}")

    async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("17. Chat function called", flush=True)
        chat_id = update.message.chat.id

        if chat_id not in messages_by_chat_id:
            messages_by_chat_id[chat_id] = []

        chat_messages = messages_by_chat_id[chat_id]

        if update.message:
            try:
                current_datetime = update.message.date
                user_first_name = update.message.from_user.first_name
                user_last_name = update.message.from_user.last_name or ""
                user_full_name = f"{user_first_name} {user_last_name}".strip()
                user_message_text = update.message.text

                formatted_user_message = {'role': 'user', 'content': f"{user_full_name}: {user_message_text}"}
                print(f"18. Received message: {user_message_text[:50]}...", flush=True)

                insert_message(conn, (user_full_name, current_datetime, user_message_text))
                chat_messages.append(formatted_user_message)
                
                if len(chat_messages) > MAX_MESSAGES:
                    chat_messages = chat_messages[-MAX_MESSAGES:]
                    messages_by_chat_id[chat_id] = chat_messages

                if re.search(r'fiji', user_message_text, re.IGNORECASE):
                    print("19. Fiji keyword found", flush=True)
                    try:
                        ai_response = await call_openai_api(
                            api_model=ai_model,
                            command=user_message_text,
                            conversation_history=chat_messages
                        )

                        formatted_ai_response = remove_prefix_case_insensitive(ai_response, "Fiji: ")
                        formatted_ai_response = formatted_ai_response.replace('\\n', ' ').replace('\n', ' ')

                        assistant_message = {'role': 'assistant', 'content': f"Fiji: {formatted_ai_response}"}
                        chat_messages.append(assistant_message)
                        
                        time_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
                        insert_message(conn, ("Fiji", time_now, formatted_ai_response))
                        
                        print("20. Sending response to user", flush=True)
                        await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)

                    except error.RetryAfter as e:
                        print(f"Rate limit error: {str(e)}", flush=True)
                        await asyncio.sleep(e.retry_after)
                        await context.bot.send_message(chat_id=chat_id, text=formatted_ai_response)
                    except Exception as e:
                        print(f"Error in chat function: {str(e)}", flush=True)
                        logger.error(f"Error processing message: {e}")
                        await context.bot.send_message(chat_id=chat_id, text="Sorry, I encountered an error.")

            except Exception as e:
                print(f"Error in message handling: {str(e)}", flush=True)
                logger.error(f"Error in chat handler: {e}")
                await context.bot.send_message(chat_id=chat_id, text="Sorry, something went wrong.")

    async def skip_past_updates(application: Application):
        print("21. Skipping past updates", flush=True)
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

    def main():
        print("22. Starting main...", flush=True)
        try:
            print("23. Creating application builder...", flush=True)
            application = ApplicationBuilder().token(
                os.getenv('TELEGRAM_BOT_TOKEN')
            ).post_init(skip_past_updates).build()
            print("24. Application built", flush=True)

            print("25. Adding handlers...", flush=True)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
            application.add_handler(CommandHandler('test', test_webhook))
            application.add_handler(CommandHandler('fixfiji', reset_command))
            application.add_handler(CommandHandler('current_version', current_version_command))
            print("26. Handlers added", flush=True)

            print("27. Starting polling...", flush=True)
            application.run_polling(drop_pending_updates=True)
            print("28. Polling started", flush=True)

        except Exception as e:
            print(f"ERROR in main: {str(e)}", flush=True)
            logger.error(f"Critical error starting bot: {e}")
            raise

    if __name__ == '__main__':
        print("29. Entering main block...", flush=True)
        while True:
            try:
                main()
            except Exception as e:
                print(f"CRASH: {str(e)}", flush=True)
                logger.error(f"Bot crashed: {e}")
                print("Restarting in 10 seconds...", flush=True)
                time.sleep(10)

except Exception as e:
    print(f"STARTUP ERROR: {str(e)}", flush=True)
    if logger:
        logger.error(f"Startup error: {e}")
    raise