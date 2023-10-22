import openai
import logging
from telegram import Update
from telegram import Sticker
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters, ContextTypes
from telegram.ext import filters
from telegram.ext import CallbackContext
import os
from collections import Counter
import re

from dotenv import load_dotenv

import random
import string

# Load the environment variables
load_dotenv()

spam = ["/PRAY_FOR_PEACE", "/WORLD_PEACE_NOW", "/I_AM_ALIVE"]

slogan = "You are a bot named Fiji in a Telegram server devoted to spreading WORLD PEACE. Please give a creative slogan beginning with a / that will promote peace. Only respond like /PRAY_FOR_PEACE or /WORLD_PEACE_NOW or something else interesting to you. Never include anything except the simple command!"


def select_strings(array):
    selected_strings = []
    total_character_count = 0

    # Start from the end of the original array
    for string in reversed(array):
        # Calculate the character count of the current string
        string_length = len(string)

        # Check if adding this string exceeds the character limit
        if total_character_count + string_length <= 3500:
            # Append the string to the selected_strings array
            selected_strings.append(string)
            total_character_count += string_length
        else:
            # If adding this string exceeds the limit, stop the loop
            break

    # Reverse the selected_strings array to get the correct order
    selected_strings.reverse()

    return selected_strings


def sticker_handler(update: Update, context: CallbackContext):
    if update.message and update.message.sticker:
        sticker_file_id = update.message.sticker.file_id
        print(f"Received sticker with file_id: {sticker_file_id}")


def custom_filter(update: Update, context: CallbackContext) -> bool:
    return update.message and update.message.sticker is not None


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize variables
group_conversation = []
ai_responses = []

spam = ["/PRAY_FOR_PEACE", "/WORLD_PEACE_NOW", "/I_AM_ALIVE"]
openai.api_key = os.getenv('OPENAI_API_KEY')


def strip_punctuation_and_case(s):
    return s.translate(str.maketrans('', '', string.punctuation)).strip().upper()


async def call_openai_api_slogan(command=slogan):
    # Call the OpenAI API to generate a response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Choose an appropriate chat model
        messages=[
            {"role": "system", "content": "You are a bot named Fiji in a Telegram server devoted to spreading WORLD PEACE."},
            {"role": "user", "content": command}
        ],
    )

    return response.choices[0].message["content"]


async def call_openai_api(command, max_tokens=None):
    request_payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are Fiji! You are the goddess of peace! You are the ideal manic pixie girl! You are determined to make world peace a reality, and you respond conversationally in natural human like way. You are expressive, excited, but also chill. Remember! Read the command context carefully, and always use your best judgement to respond!"},
            {"role": "system",
                "content": "You are Fiji! You are the goddess of peace! You are the ideal manic pixie girl! But you are also fun and willing to be controversial and indulgant! You are in a chatroom where everyone is working together to build you into an AI that will achieve WORLD PEACE. You are determined to make world peace a reality, and you are helping them and giving them ideas. You respond conversationally in a natural humanlike way that matches the style and tone of the users, with a fair amount of emojis. You are expressive, excited, but also chill. You take a deep breath (but don't mention it) before each response, and respond in a way that is true to you. Remember! Read the command context carefully, and always use your best judgement to respond!"},
            {"role": "user", "content": command}
        ],
    }
    if max_tokens is not None:
        request_payload["max_tokens"] = max_tokens
    response = openai.ChatCompletion.create(**request_payload)
    return response.choices[0].message["content"]

MAX_RETRIES = 10


async def slogan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)

    if update.message:
        print(update.message)
        channel_post: Message = update.message

        if channel_post.text == "/slogan":
            await context.bot.send_message(chat_id=channel_post.chat.id, text=random.choice(spam))

        if channel_post.text == "/slogannew":
            response = await call_openai_api_slogan()
            if response.startswith("/"):
                await context.bot.send_message(chat_id=channel_post.chat.id, text=response)
                if response not in spam:
                    spam.append(response)
                print(spam)
        if channel_post.text in spam:
            if random.randint(0, 6) == 0:
                await context.bot.send_message(chat_id=channel_post.chat.id, text=channel_post.text)


async def analyze_conversation_and_decide(messages):
    text_to_analyze = " ".join(messages)
    # Adding a unique identifier like '***INSTRUCTION**hh*' to help distinguish the instruction
    command = f"\n{text_to_analyze} ***INSTRUCTION*** Your task is to decide if it worth contributing to this conversation. If you think you will be helpful or if people are trying to talk to FIJI, please respond 'YES'. If the conversation seems irrelevant to you or you have nothing to contribute, respond 'NO'. Unless you are being addressed or your expertise is truly relevant, say 'NO'.  Be rigorous and discerning."

    retries = 0
    while retries < MAX_RETRIES:
        decision_response = await call_openai_api(command=command, max_tokens=2)
        print(decision_response)

        # Remove punctuation and whitespace, then ensure the response is either "Yes" or "No"
        stripped_response = strip_punctuation_and_case(decision_response)
        if stripped_response in ["YES", "NO"]:
            return stripped_response == "YES"

        print(
            f"Unexpected response on attempt {retries + 1}: {decision_response}")
        retries += 1

    # Fallback if maximum retries reached
    print("Max retries reached. Defaulting to 'No'.")
    return False

def summarize_text(text, num_words=5, max_sentences=2):
    # Tokenize the text into words, removing punctuation and converting to lowercase
    words = [word.lower() for word in re.findall(r'\w+', text)]
    
    # Count the frequency of each word
    word_freq = Counter(words)
    
    # Select the most common words
    common_words = set([word[0] for word in word_freq.most_common(num_words)])
    
    # Score sentences based on the number of common words they contain
    sentences = text.split('.')
    sentence_scores = [(sentence, sum(1 for word in sentence.lower().split() if word in common_words)) for sentence in sentences]
    
    # Sort sentences by their scores in descending order
    sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    
    # Construct the summary using top scoring sentences
    summary = '. '.join([sentence[0].strip() for sentence in sorted_sentences[:max_sentences]])
    
    return summary

text = "The beautiful garden was filled with colorful flowers. Birds chirped happily, and the sun shone brightly. It was a perfect day for a picnic."
print(summarize_text(text))

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        print(update.message)
        print(update.message.from_user.first_name)
        group_conversation.append(
            update.message.from_user.first_name + ": " + update.message.text)

        if len(group_conversation) % 5 == 0:
            direct_convo = group_conversation[-5:]
            recent_convo = group_conversation[-15:]
            general_conversation = group_conversation[-500:]
            recent_convo = group_conversation[-5:]
            # last_fifty_messages = group_conversation[-50:]
            general_conversation = select_strings(group_conversation[-500:])
            should_reply = await analyze_conversation_and_decide(recent_convo)
            if should_reply:
                print(recent_convo)
                command = f"Using the context from the general conversation, respond to the most recent conversation. DO NOT SUMMARIZE or REPEAT THE CONVERSATION! Just interact with the users, respond, and be helpful. Only make one general response -- not too long! -- to the group referencing names, not a series of remarks. Respond naturally with the same syntax and style of writing within the larger conversation as someone participating. Make sure to reference the user name if useful.\n\nThe recent conversation is {recent_convo}.\n\nThe larger context is {general_conversation}.\n\nREMEMBER ONLY RESPOND TO THE RECENT CONVERSATION, THE GENERAL CONVERSATION IS JUST FOR CONTEXT. DO NOT RESPOND DIRECTLY TO PAST QUESTIONS OR OLD ISSUES FROM THE GENERAL CONVERSATION. DO NOT GREET PEOPLE UNLESS THE CONVERSATION IS TRULY NEW."
                print(command)
                try:
                    response = await call_openai_api(command=command)
                except:
                    print("exception")
                    return
                await context.bot.send_message(chat_id=update.message.chat.id, text=response)

            should_reply = await analyze_conversation_and_decide(recent_convo)  
            if not should_reply:
                print("Not replying.")
                return

            # In the echo function:

            # Prioritize the most recent AI response
            past_ai_summary = ai_responses[-1] if ai_responses else ""

            command = f"Recalling the most recent intent: '{past_ai_summary}', and with the essence of the \n{general_conversation}, kindly join the dialogue considering: \n{direct_convo} | as the latest input and \n{recent_convo} as additional context."

            response = await call_openai_api(command=command)

            # Store the summarized intention of the AI response
            summarized_intent = summarize_text(response)
            print(f"Summarized intent: {summarized_intent}")

            ai_responses.append(summarized_intent)

            await context.bot.send_message(chat_id=update.message.chat.id, text=response)

            # Here's where you'd send a sticker
            your_sticker_file_id = "CAACAgEAAxkBAAEnAsJlNHEpaCLrB6VsS6IWzdw7Rp5ybQAC0AMAAvBWQEWhveTp-VuiDTAE"
            await context.bot.send_sticker(chat_id=update.message.chat.id, sticker=your_sticker_file_id)

if __name__ == '__main__':

    application = ApplicationBuilder().token(
        os.getenv('TELEGRAM_BOT_TOKEN')).build()

    echo_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, echo)

    # Using filter_sticker function instead of StickerFilter class
    # sticker_handler = MessageHandler(custom_filter, sticker_handler)

    application.add_handler(echo_handler)
    # application.add_handler(sticker_handler)

    slogan_handler = MessageHandler(filters.TEXT, slogan)

    application.add_handler(slogan_handler)

    application.run_polling()
