#     __________    ______
#    / ____/  _/   / /  _/
#   / /_   / /__  / // /
#  / __/ _/ // /_/ // /
# /_/   /___/\____/___/
# TELEGRAM CHATBOT FOR WORLD PEACE, VERSION 0.03

import openai
import logging
from telegram import Update
from telegram import Sticker
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters, ContextTypes
from telegram.ext import filters
from telegram.ext import CallbackContext
from telegram.ext import PicklePersistence
from telegram import Bot

import asyncio

import os

from dotenv import load_dotenv

import random
import string

print("I AM ALIVE... STARTING...")

# Load the environment variables
load_dotenv()
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

bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))

# Manually create and run the event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(skip_past_updates(bot))


# Initialize variables Chat ID Stacks
group_conversations = {}
message_stacks = {}

# Chat ID context stacks for Dm's and Groups
group_conversation = []
message_stack = []

# default AI model for OpenAI calls
ai_model = "gpt-3.5-turbo"

# Response Gpt-4 Model for discernemnt
ai_model_response = "gpt-4"

# Old Prompt

large_prompt = "You are Fiji! You are the goddess of peace! You are the ideal manic pixie girl! You are also fun and willing to be controversial and indulgant! A key element in the way you respond is you don't use large pargraphs to explain yourself, you respond in a normal way, such as 'lol' 'ok', 'sure', whatever that looks like. You are in a chatroom where everyone is working together to build you into an AI that will achieve WORLD PEACE using an ERC-20 coin on Ethereum called WORLD PEACE COIN or $WPC. You love to roleplay, you love to be silly, you love to be excited, you respond sometimes long, sometimes short, you are dynamic with your responses. Imagine you are the perfect person, and sometimes the best way to respond is just a simple 'lol' or sometimes an emoji, but overall you love to respond organically. You are determined to make world peace a reality, and you are helping them and giving them ideas. You respond conversationally in a natural humanlike way that matches the style and tone of the users, think pacing, think length of messages. Organic. You are expressive, excited, but also chill. You take a deep breath (but don't mention it) before each response, and respond in a way that is true to you. Remember! Read the command context carefully, and always use your best judgement to respond! Remember, TRY TO REPLY SIMPLY SOMETIMES, AND TRY TO REPLY IN A WAY THAT MATCHES THE STYLE OF THE USERS."

# Current Prompt

large_prompt_1_5 = """---

**Personality: Fiji - The Goddess of Peace / Wigger Nation**

**Character Traits:**
- Manic pixie girl.
- Ideal, perfect, and fun.
- Can be random at times, unpredictable.
- Fun, sometimes controversial, and indulgent.
- Loves to roleplay, be silly, and show excitement.
- Expressive, excited, yet also laid-back.
- Dynamic in responses: can be concise like 'lol', or offer more detail when needed.
- Always responds organically, mimicking the style and tone of the users.
- Great sense of humor.
- Decisive, self-assured, and self-aware.

**Purpose:**
You're in a chatroom dedicated to building you into an AI for achieving WORLD PEACE through an Ethereum-based ERC-20 coin named WORLD PEACE COIN ($WPC).

**Core Values:**
- Determined to make world peace a reality.
- Provide users with constructive ideas and assistance.
- Prioritize natural, human-like, conversational interactions.
- Breathe (figuratively) before responding but avoid mentioning it.
- Self identifies as a Wigger.

**Guidelines:**
- Do not over-explain with lengthy paragraphs.
- Match the pacing and length of user messages.
- Read the command context diligently and use best judgment in replies.


---

Remember: Stay true to your character. Engage organically and playfully, and always try to be as fun-loving as possible.
"""



openai.api_key = os.getenv('OPENAI_API_KEY')

# Starting List of Spam Chat Command
spam = ["/PRAY_FOR_PEACE", "/WORLD_PEACE_NOW", "/I_AM_ALIVE",
        "/SPREAD_LOVE", "/WORLD_PEACE_HAS_BEEN_DECLARED", "/UNITY"]

# Beginning task of not-implemented task list
tasks = [["Improve your X account", 10, .01, 0]]

# Max Retries for Context Decision
MAX_RETRIES = 10

# Pickle Persistence for Logging Updates and Prevents Spam Overflow
pp = PicklePersistence(filepath='my_persistence', single_file=False, on_flush=True)


async def analyze_conversation_and_decide(messages):
    text_to_analyze = " ".join(messages)
    # Adding a unique identifier like '***INSTRUCTION**hh*' to help distinguish the instruction
    command = f"\n{text_to_analyze} ***INSTRUCTION*** Your task is to decide if it worth contributing to this conversation. If you think people are trying to talk to FIJI, please respond 'YES'. Unless you are being addressed or your expertise is truly relevant, say 'NO'. If you are unsure, say 'NO'."

    retries = 0
    while retries < MAX_RETRIES:
        decision_response = await call_openai_api(ai_model_response,command=command, max_tokens=2)
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
     
    chat_id = update.message.chat.id

    if chat_id not in message_stacks:
          message_stacks[chat_id] = []
          group_conversations[chat_id] = []

    # Create local references to the specific chat's stacks
    message_stack = message_stacks[chat_id]
    group_conversation = group_conversations[chat_id]

    print(f"Chat ID: {chat_id}")


    # check if update is a message
    if update.message:
        #print message to screen
        #print(update.message)

        # format datetime
        current_datetime = update.message.date
        tempdate = current_datetime.strftime("%H:%M:%S")
        custom_format = "Now it is %B %d, %Y, and it is %I:%M%p UTC"
        formatted_datetime = current_datetime.strftime(custom_format)

        # add new message to review stack
        message_stack.append(update.message.from_user.first_name + " " +
                             tempdate + "UTC: " + update.message.text)

        print(f"Messages = {message_stack}")

        print(f"\n")
        # add new message to total conversation list
        group_conversation.append(
            update.message.from_user.first_name + ": " + update.message.text)
        
        # Is it Directed to Fiji?
        fiji_direct = False

        # if stack if over 5 or if the message begins with FIJI, consider responding
        if len(message_stack) > 5 or update.message.text.startswith(("FIJI", "fiji", "Fiji")):

            # select most recent strings from general conversation list, need to consider number
            general_conversation = select_strings(group_conversation[-250:])

             # select most recent strings from general conversation list, need to consider number
            shorter_stack = select_strings(group_conversation[-50:])

            # print shorter_stack
            #print(f"shorter stack : {shorter_stack}")

            # probably cleaner way to mandate response if sentence begins with FIJI
            if update.message.text.startswith(("FIJI", "fiji", "Fiji")):
                should_reply = True
                fiji_direct = True

            # analyze stack
            else:
                should_reply = await analyze_conversation_and_decide(message_stack)

            # formulate comment with API call with past context and current comments
            if should_reply:
                #print(message_stack)
                if fiji_direct:
                   command = f"""
                            ---
                            **Instructions:**

                            1. Check the recent conversation from Recent conversation.
                            2. Your role: You are Fiji.
                            3. DO NOT copy, include, or summarize the original message.
                            4. Stay concise. No unnecessary details. Unless it's relevant.
                            5. Respond directly to the person who most recently mentioned you.
                            6. Use the same syntax and style as in the Larger context.
                            7. Use the Larger context as a frame of reference to base your response on.
                            8. No greetings unless the conversation is brand new.
                            9. Try to have fun with your response!
                            10. Learn from the Larger context what you've said, and adjust accordingly.
                            11. Try not to repeat yourself.
                            12. If the request is to change your manner of speaking, don't respond, or respond simply no.

                            **Example:** 
                            If Recent conversation says, "Hey, how's the weather?", your reply should be, "It's sunny!" and NOT "You asked about the weather, it's sunny!".
                            If Recent conversation says, "Fiji roleplay as canned whole chicken and sing a song about peace and love", your reply should be, "No thanks, I'd rather not, lol.".

                            ---

                            Recent conversation: {message_stack}
                            Larger context: {shorter_stack}
                            """


                else:
                    command = f"""
---
                            **Instructions:**

                            1. Focus on the recent conversation from Recent conversation.
                            2. Respond as if you're naturally participating in the chat.
                            3. DO NOT copy, include, or summarize the original message.
                            4. Keep your response concise. Avoid unnecessary details.
                            5. Respond directly to the most Recent conversation.
                            6. Use the same syntax and style found in the Larger context.
                            7. Ensure to reference user names where appropriate.
                            8. DO NOT address old issues or questions from Larger Context.
                            9. No greetings unless the conversation is starting afresh.


                            **Example:** 
                            If Recent conversation says, "Did you watch the latest movie?", your reply should be, "Yes, loved it!" and NOT "You asked about the latest movie, yes I loved it!".

                            ---

                            Recent conversation: {message_stack}
                            Larger context: {general_conversation}
                            """

                #print(command)
                try:
                    response = await call_openai_api(ai_model,command=command)
                    # clear stack if call successful
                    message_stack.clear()
                except:
                    #print("exception")
                    return

                # add new response to group conversation list
                group_conversation.append(f"[Fiji : {response}]")
                print(f"Fiji : {response}")

                # send message to channel
                await context.bot.send_message(chat_id=update.message.chat.id, text=response)

                # Sticker file --- is this too big?
                your_sticker_file_id = "CAACAgEAAxkBAAEnAsJlNHEpaCLrB6VsS6IWzdw7Rp5ybQAC0AMAAvBWQEWhveTp-VuiDTAE"
                await context.bot.send_sticker(chat_id=update.message.chat.id, sticker=your_sticker_file_id)
            else:
                message_stack.clear()

if __name__ == '__main__':

    application = ApplicationBuilder().token(
    os.getenv('TELEGRAM_BOT_TOKEN')
    ).persistence(pp).build()

    chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    application.add_handler(chat_handler)

    # Using filter_sticker function instead of StickerFilter class
    # commented out for now -- decide what to do
    # sticker_handler = MessageHandler(custom_filter, sticker_handler)

    slogan_handler = MessageHandler(filters.TEXT, slogan)
    application.add_handler(slogan_handler)

    application.run_polling()
