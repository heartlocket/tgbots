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


async def call_openai_api(command, max_tokens=None):
    request_payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are Fiji! You are the goddess of peace! You are the ideal manic pixie girl! You are determined to make world peace a reality, and you respond conversationally in natural human like way. You are expressive, excited, but also chill. Remember! Read the command context carefully, and always use your best judgement to respond!"},
            {"role": "user", "content": command}
        ],
    }
    if max_tokens is not None:
        request_payload["max_tokens"] = max_tokens
    response = openai.ChatCompletion.create(**request_payload)
    return response.choices[0].message["content"]

MAX_RETRIES = 10

async def analyze_conversation_and_decide(messages):
    text_to_analyze = " ".join(messages)
    # Adding a unique identifier like '***INSTRUCTION**hh*' to help distinguish the instruction
    command = f"\n{text_to_analyze} ***INSTRUCTION*** Your task is to decide if you should contribute to this conversation. Please respond only with 'YES' or 'NO'."

    retries = 0
    while retries < MAX_RETRIES:
        decision_response = await call_openai_api(command=command, max_tokens=2)
        print(decision_response)

        # Remove punctuation and whitespace, then ensure the response is either "Yes" or "No"
        stripped_response = strip_punctuation_and_case(decision_response)
        if stripped_response in ["YES", "NO"]:
            return stripped_response == "YES"

        print(f"Unexpected response on attempt {retries + 1}: {decision_response}")
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
        group_conversation.append(update.message.text)

        if len(group_conversation) % 5 == 0:
            direct_convo = group_conversation[-5:]
            recent_convo = group_conversation[-15:]
            general_conversation = group_conversation[-500:]

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
    #sticker_handler = MessageHandler(custom_filter, sticker_handler)

    application.add_handler(echo_handler)
    #application.add_handler(sticker_handler)

    application.run_polling()