# court.py
# Import necessary modules
from telegram.ext import Updater, ApplicationBuilder, MessageHandler, CallbackContext, filters, ContextTypes, CommandHandler
import openai
import os
from telegram import Bot
from dotenv import load_dotenv
from datetime import datetime, timezone

message_history = []

openai.api_key = os.getenv('OPENAI_API_KEY')


def create_bot_application(token):
    return ApplicationBuilder().token(token).build()

load_dotenv()

JUDGE_TOKEN = os.getenv("JUDGEBOT_TOKEN")
PLATNIFF_TOKEN = os.getenv("PLAINTIFFBOT_TOKEN")
DEFENDANT_TOKEN = os.getenv("DEFENDANTBOT_TOKEN")
JUROR_TOKEN = os.getenv("JURORBOT_TOKEN")

print("BEGING COURT CASE...")



judge_bot = Bot(token=JUDGE_TOKEN)
plaintiff_bot =  Bot(token=PLATNIFF_TOKEN)
defendant_bot = Bot(token=DEFENDANT_TOKEN)
juror_bot = Bot(token=JUROR_TOKEN)

# Create applications for each bot
judge_application = create_bot_application(JUDGE_TOKEN)
plaintiff_application = create_bot_application(PLATNIFF_TOKEN)
defendant_application = create_bot_application(DEFENDANT_TOKEN)
juror_application = create_bot_application(JUROR_TOKEN)

ai_model = "gpt-4-1106-preview"



def generate_response(prompt):
   response = openai.ChatCompletion.create(
        model=ai_model,  # Choose an appropriate chat model
        messages=[
            {"role": "system", "content": "Helpful Ai"},
            {"role": "user", "content": prompt}
        ],
    )
   return response.choices[0].message["content"]



def add_message_to_history(sender_name, message):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted_message = f"{sender_name} {timestamp}: {message}"
    message_history.append(formatted_message)
    print(message_history)


async def send_bot_message(bot, chat_id, text):
    await bot.send_message(chat_id=chat_id, text=text)
    bot_info = await bot.get_me()
    display_name = bot_info.full_name 
    add_message_to_history(display_name, text)



async def start_court(update, context):
    try:
        main_user_username = context.args[0]
        if main_user_username.startswith('@'):
            main_user_username = main_user_username[1:]  # Remove '@' if present
    except IndexError:
        await send_bot_message(judge_bot, update.message.chat_id, "Please provide a username. Usage: /startcourt @[username]")
        return

    context.chat_data['main_user'] = main_user_username
    context.chat_data['court_state'] = 1  # Court session started
    await send_bot_message(judge_bot, update.message.chat_id, f"Court is now in session, @{main_user_username} please present your case.")


async def handle_user_message(update, context):
    # Extract user information and message
    user = update.message.from_user
    user_name = user.full_name if user.full_name else user.username
    user_message = update.message.text

    # Add message to history
    add_message_to_history(user_name, user_message)

    # Check the court state and handle accordingly
    if context.chat_data.get('court_state') == 1:
        # Check if the message is from the main user
        if update.message.from_user.username == context.chat_data.get('main_user'):
            # Store user's messages (you can append to a list in chat_data)
            if 'user_testimony' not in context.chat_data:
                context.chat_data['user_testimony'] = []
            context.chat_data['user_testimony'].append(update.message.text)
    # ... Further processing based on your application's logic ...


async def done_command(update, context):
    print("Done Command Called")
    if context.chat_data.get('court_state') == 1:
        # Check if the command is from the main user
        if update.message.from_user.username == context.chat_data.get('main_user'):
            # Transition to next stage
            context.chat_data['court_state'] = 2
            # Here, you can process the testimony and involve the Judge bot
            # For example, use OpenAI to summarize the case
            # ...
            await send_bot_message(judge_bot, update.message.chat_id, "Thank you for your testimony. The court will now deliberate.")


def main():
    # Adding handlers to each application
    judge_application.add_handler(CommandHandler('startcourt', start_court))
    judge_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    judge_application.add_handler(CommandHandler('done', done_command))

    # Add similar handlers for other applications as needed

    # Run each application
    judge_application.run_polling()
    plaintiff_application.run_polling()
    defendant_application.run_polling()
    juror_application.run_polling()

if __name__ == "__main__":
    main()