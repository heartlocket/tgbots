#     __________    ______
#    / ____/  _/   / /  _/
#   / /_   / /__  / // /
#  / __/ _/ // /_/ // /
# /_/   /___/\____/___/
# TELEGRAM CHATBOT FOR WORLD PEACE, VERSION 0.01

import openai
import logging
from telegram import Update
from telegram import Sticker
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters, ContextTypes
from telegram.ext import filters
from telegram.ext import CallbackContext
import os

from dotenv import load_dotenv

import random
import string

# Load the environment variables
load_dotenv()


# logging formatting
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize variables
group_conversation = []
message_stack = []

# default AI model for OpenAI calls
ai_model = "gpt-3.5-turbo"
openai.api_key = os.getenv('OPENAI_API_KEY')

# Starting List of Spam Chat Command
spam = ["/PRAY_FOR_PEACE", "/WORLD_PEACE_NOW", "/I_AM_ALIVE",
        "/SPREAD_LOVE", "/WORLD_PEACE_HAS_BEEN_DECLARED", "/UNITY"]

# Beginning task of not-implemented task list
tasks = [["Improve your X account", 10, .01, 0]]

# Max Retries for Context Decision
MAX_RETRIES = 10


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


def custom_filter(update: Update, context: CallbackContext) -> bool:
    return update.message and update.message.sticker is not None


def strip_punctuation_and_case(s):
    return s.translate(str.maketrans('', '', string.punctuation)).strip().upper()


# OpenAI call to make new slogan
async def call_openai_api_slogan():

    # Slogan instructions
    slogan = "You are a bot named Fiji in a Telegram server devoted to spreading WORLD PEACE. Please give a creative slogan beginning with a / that will promote peace. Only respond like /PRAY_FOR_PEACE or /WORLD_PEACE_NOW or something else interesting to you. Never include anything except the simple command!"

    # Call the OpenAI API to generate a response
    response = openai.ChatCompletion.create(
        model=ai_model,  # Choose an appropriate chat model
        messages=[
            {"role": "system", "content": "You are a bot named Fiji in a Telegram server devoted to spreading WORLD PEACE."},
            {"role": "user", "content": slogan}
        ],
    )

    return response.choices[0].message["content"]


async def call_openai_api(command, max_tokens=None):
    request_payload = {
        "model": ai_model,
        "messages": [
            {"role": "system",
                "content": "You are Fiji! You are the goddess of peace! You are the ideal manic pixie girl! But you are also fun and willing to be controversial and indulgant! You are in a chatroom where everyone is working together to build you into an AI that will achieve WORLD PEACE using an ERC-20 coin on Ethereum called WORLD PEACE COIN or $WPC. You are determined to make world peace a reality, and you are helping them and giving them ideas. You respond conversationally in a natural humanlike way that matches the style and tone of the users, with a fair amount of emojis. You are expressive, excited, but also chill. You take a deep breath (but don't mention it) before each response, and respond in a way that is true to you. Remember! Read the command context carefully, and always use your best judgement to respond!"},
            {"role": "user", "content": command}
        ],
    }
    if max_tokens is not None:
        request_payload["max_tokens"] = max_tokens
    response = openai.ChatCompletion.create(**request_payload)
    return response.choices[0].message["content"]


async def slogan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)

    if update.message:
        print(update.message)
        channel_post: Message = update.message

        # send random spam command from list
        if channel_post.text == "/slogan":
            await context.bot.send_message(chat_id=channel_post.chat.id, text=random.choice(spam))

        # add new slogan
        if channel_post.text == "/slogannew":
            response = await call_openai_api_slogan()
            if response.startswith("/"):
                await context.bot.send_message(chat_id=channel_post.chat.id, text=response)
                if response not in spam:
                    spam.append(response)

        # RANDOMLY ECHO SPAM IN YOUR LIST
        if channel_post.text in spam:
            if random.randint(0, 6) == 0:
                await context.bot.send_message(chat_id=channel_post.chat.id, text=channel_post.text)

# function to decide whether to comment, hacky now, need to learn best practices for this


async def analyze_conversation_and_decide(messages):
    text_to_analyze = " ".join(messages)
    # Adding a unique identifier like '***INSTRUCTION**hh*' to help distinguish the instruction
    command = f"\n{text_to_analyze} ***INSTRUCTION*** Your task is to decide if it worth contributing to this conversation. If you think people are trying to talk to FIJI, please respond 'YES'. Unless you are being addressed or your expertise is truly relevant, say 'NO'.  Be rigorous. Most of the time you respond 'NO'!"

    retries = 0
    while retries < MAX_RETRIES:
        decision_response = await call_openai_api(command=command, max_tokens=2)
        print(decision_response)

        # Remove punctuation and whitespace, then ensure the response is either "Yes" or "No"
        stripped_response = strip_punctuation_and_case(decision_response)
        if stripped_response.startswith("YES"):
            return True
        if stripped_response.startswith("NO"):
            return False

        print(
            f"Unexpected response on attempt {retries + 1}: {decision_response}")
        retries += 1

    # Fallback if maximum retries reached
    print("Max retries reached. Defaulting to 'No'.")
    return False


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check if update is a message
    if update.message:
        # print message to screen
        print(update.message)

        # format datetime
        current_datetime = update.message.date
        tempdate = current_datetime.strftime("%H:%M:%S")
        custom_format = "Now it is %B %d, %Y, and it is %I:%M%p UTC"
        formatted_datetime = current_datetime.strftime(custom_format)

        # add new message to review stack
        message_stack.append(update.message.from_user.first_name + " " +
                             tempdate + "UTC: " + update.message.text)

        # add new message to total conversation list
        group_conversation.append(
            update.message.from_user.first_name + ": " + update.message.text)

        # if stack if over 5 or if the message begins with FIJI, consider responding
        if len(message_stack) > 5 or update.message.text.startswith(("FIJI", "fiji", "Fiji")):

            # select most recent strings from general conversation list, need to consider number
            general_conversation = select_strings(group_conversation[-500:])

            # probably cleaner way to mandate response if sentence begins with FIJI
            if update.message.text.startswith(("FIJI", "fiji", "Fiji")):
                should_reply = True

            # analyze stack
            else:
                should_reply = await analyze_conversation_and_decide(message_stack)

            # formulate comment with API call with past context and current comments
            if should_reply:
                print(message_stack)
                command = f"{formatted_datetime}. Using the context from the general conversation, respond to the most recent conversation. DO NOT SUMMARIZE or REPEAT THE CONVERSATION! DO NOT INCLUDE THE DATETIME UNLESS IT IS NEEDED! Just interact with the users, respond, and be helpful. Only make one general response -- not too long! -- to the group referencing names, not a series of remarks. Respond naturally with the same syntax and style of writing within the larger conversation as someone participating. Make sure to reference the user name if useful.\n\nThe recent conversation is {message_stack}.\n\nThe larger context is {general_conversation}.\n\nREMEMBER ONLY RESPOND TO THE RECENT CONVERSATION, THE GENERAL CONVERSATION IS JUST FOR CONTEXT. DO NOT RESPOND DIRECTLY TO PAST QUESTIONS OR OLD ISSUES FROM THE GENERAL CONVERSATION. DO NOT GREET PEOPLE UNLESS THE CONVERSATION IS TRULY NEW."
                print(command)
                try:
                    response = await call_openai_api(command=command)
                    # clear stack if call successful
                    message_stack.clear()
                except:
                    print("exception")
                    return

                # add new response to group conversation list
                group_conversation.append(f"FIJI: {response}")

                # send message to channel
                await context.bot.send_message(chat_id=update.message.chat.id, text=response)

                # Sticker file --- is this too big?
                your_sticker_file_id = "CAACAgEAAxkBAAEnAsJlNHEpaCLrB6VsS6IWzdw7Rp5ybQAC0AMAAvBWQEWhveTp-VuiDTAE"
                await context.bot.send_sticker(chat_id=update.message.chat.id, sticker=your_sticker_file_id)
            else:
                message_stack.clear()

if __name__ == '__main__':

    application = ApplicationBuilder().token(
        os.getenv('TELEGRAM_BOT_TOKEN')).build()

    chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    application.add_handler(chat_handler)

    # Using filter_sticker function instead of StickerFilter class
    # commented out for now -- decide what to do
    # sticker_handler = MessageHandler(custom_filter, sticker_handler)

    slogan_handler = MessageHandler(filters.TEXT, slogan)
    application.add_handler(slogan_handler)

    application.run_polling()
