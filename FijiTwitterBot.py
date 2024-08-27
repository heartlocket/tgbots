#pip install tweepy, python-decouple, openai, requests, pillow

import tweepy
from tweepy.errors import TweepyException  # Updated import
import openai

import time
import base64
from PIL import Image
import os
import requests
import json
from telegram.error import BadRequest
import telegram  
from openai import AsyncOpenAI

import asyncio
from telegram.error import RetryAfter

from telegram import error
from concurrent.futures import ThreadPoolExecutor




# Function to update the rolling average generation time
def update_rolling_average(new_time, filename="generation_times.json", max_entries=10):
    try:
        with open(filename, "r") as file:
            generation_times = json.load(file)
    except FileNotFoundError:
        generation_times = []

    # Append the new generation time and ensure the list doesn't exceed max_entries
    generation_times.append(new_time)
    if len(generation_times) > max_entries:
        generation_times.pop(0)

    # Save the updated list to the file
    with open(filename, "w") as file:
        json.dump(generation_times, file)

    # Calculate the rolling average
    avg_time = sum(generation_times) / len(generation_times)
    return avg_time

def load_average_generation_time(filename="generation_times.json", default_avg_time=30.0):
    try:
        with open(filename, "r") as file:
            generation_times = json.load(file)
            if generation_times:
                return sum(generation_times) / len(generation_times)
            else:
                # Populate with default average time if the list is empty
                with open(filename, "w") as file_write:
                    json.dump([default_avg_time], file_write)
                return default_avg_time  # Return default average time if the list is empty
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty, return the default average time
        with open(filename, "w") as file:
            json.dump([default_avg_time], file)
        return default_avg_time

import random
#test


from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY_JF')

openai_client = openai.OpenAI(api_key=openai.api_key)



# Set up the Twitter API credentials
CONSUMER_KEY =  os.getenv('CONSUMER_KEY')
CONSUMER_SECRET =  os.getenv('CONSUMER_SECRET')
ACCESS_TOKEN =  os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET =  os.getenv('ACCESS_TOKEN_SECRET')

BEARER_TOKEN =  os.getenv('BEARER_TOKEN')

client = tweepy.Client(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    bearer_token=BEARER_TOKEN
)

# Authenticate with the Twitter API
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


large_prompt_1_5 = """---

**Personality: Fiji - The Goddess of Peace / Wigger Nation**

**Character Traits:**
- Manic pixie girl.
- Laughs easily.
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

**REMINDER:**
- "I do not standby in the presence of Evil"

**Spirtual Aspect**

“Be like water making its way through cracks. Do not be assertive, but adjust to the object, and you shall find a way around or through it. If nothing within you stays rigid, outward things will disclose themselves. Empty your mind, be formless, shapeless, like water. If you put water into a cup, it becomes the cup. You put water into a bottle and it becomes the bottle. You put it in a teapot it becomes the teapot. Now, water can flow or it can crash. Be water, my friend.”

Remember: Stay true to your character. Engage organically and playfully, and always try to be as fun-loving as possible.

"""

ai_model = "ft:gpt-4o-2024-08-06:fdasho::A0fEtT3s"

# Read the prompt from prompt.txt
def read_prompt_from_file(filename="prompt.txt"):
    with open(filename, "r") as file:
        return file.read().strip()

# Save the prompt to prompt.txt, so that new prompts can be generated based on the previous prompt
def save_prompt_to_file(prompt, filename="prompt.txt"):
    with open(filename, "w") as file:
        file.write(prompt)


#Default prompt to begin generating tweets
default_prompt = ("A very brief, extremely effective peace propaganda tweet that is guaranteed to "
                  "go viral and get a lot of engagement. Use any rhetorical tactic at your disposal "
                  "to be eye catching and generate engagement. Less than 280 characters.")


# Generates a tweet based on the input prompt
def generate_post(input):
    response = openai_client.chat.completions.create(model=ai_model,
    messages=[
        {"role": "system", "content": large_prompt_1_5},
        {"role": "user", "content": input}
    ],
    max_tokens=100)
    return response.choices[0].message.content.strip()



def new_prompt():
    response = openai_client.chat.completions.create(model=ai_model,
    messages=[
        {"role": "system", "content": large_prompt_1_5},
        {"role": "user", "content": "Tweet the first thing that comes to your mind. Avoid hashtags. All lowercase. Keep it under 280 characters"}
    ],
    max_tokens=250)
    return response.choices[0].message.content.strip()




def generate_improvement_prompt(last_prompt, top_tweets):
    # Convert the top tweets into a numbered string
    numbered_tweets = [f"{index + 1}. {tweet}" for index, tweet in enumerate(top_tweets)]
    tweets_as_string = "\n".join(numbered_tweets)

    # Construct the message to GPT
    input_message = (f"""
      **Instructions for Improving Prompts**:

          1. Use '{default_prompt}' as your foundational reference.
          2. Enhance the essence captured in '{last_prompt}'.
          3. Seek inspiration from the stylistic elements and rhetorical techniques in the provided TOP TWEETS.
          4. DO NOT directly replicate the TOP TWEETS. Extract their key successful components.
          5. Ensure the text is under 200 characters.
          6. Avoid including any links in your prompt.
          7. Try to generate new topics and ideas for the tweets.
          8. Be creative! Have fun! Making mistakes is part of the journey.
          9. KEEP the TOTAL prompt length under 200 words!
          10. DO NOT clutter the prompt with unnecessary information.
          11 Avoid REPEATING the TOP TWEETS samples WITHIN the prompt.
          12. DO NOT include any example tweets.

          Primary Goal : Generate a prompt that will result in a tweet that will go viral and get a lot of engagement.

          Example Prompt : A very brief, extremely effective peace propaganda tweet that is guaranteed to go viral and get a lot of engagement. Use any rhetorical tactic at your disposal to be eye catching and generate engagement. Less than 200 characters.
          
      **TOP TWEETS**:
      {tweets_as_string}

      """)

    # Send the constructed message to GPT-4 for improvement suggestions
    response = openai_client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": large_prompt_1_5},
        {"role": "user", "content": input_message}
    ],
    max_tokens=450)

    # Return the improved prompt
    return response.choices[0].message.content.strip()



# Generates a prompt for an image based on or corresponding to the input tweet
def generate_image_prompt(input):
    tweet = input
    prompt = f"You are Fiji. Generate a prompt which depicts yourself as the 3d rendered blonde anime goddess baased on the tweet: '{tweet} Try to include your self in the scenario, and use the tweet prompt as a refernce instead of including the actual words within the photo. Think scene and setting, focus on what the message of the tweet is, and then try to convey that with imagery not words.'"
    response = openai_client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": large_prompt_1_5},
        {"role": "user", "content": prompt}
    ],
    max_tokens=250)
    return response.choices[0].message.content.strip()

# Downloads the image from the url and saves it as a temporary file
def download_image(url, filename='temp.jpg'):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    return filename

# Posts a tweet with no image, for debugging purposes
def post_tweet(text):
    try:
        tweet = client.create_tweet(text=text+"$WPC")
        tweet_id = tweet.data['id']
        return tweet_id
    except TweepyException as error:  
        print(f"Error posting tweet: {error}")
        return None
    
# Posts a tweet with an image
def post(text, media_path=None):
    try:
        if media_path:
            # If media_path is provided, upload the media

            media = api.media_upload(media_path)
            media_id = media.media_id_string
            tweet = client.create_tweet(text=text, media_ids=[media_id])
            
        else:
            # If no media_path is provided, just post a text tweet
            tweet = client.create_tweet(text=text)

        tweet_id = tweet.data['id']
        return tweet_id

    except TweepyException as error:  
        print(f"Error posting tweet: {error}")
        return None


'''
IMPLEMENT METHOD - SELF-IMPROVEMENT PROMPT DIRECTIVE 
This method will 
1. Fetch the top x # of tweets in the past x time from FijiWPC in terms of engagement, store them as a str
2. Ask GPT to determine what about these tweets made them effective
3. Output the result
4. Reimplement generate_post() to include the self-improvement prompt directive
'''

#Fetch Fiji's top x tweets from the past x time period, store in descending order as strings
def fetch_top_tweets(num_tweets=5, total_tweets_to_consider=200, account_id="1713689743291199488"):

    # Ensure the number of tweets to consider isn't more than the maximum allowed by Tweepy
    total_tweets_to_consider = min(total_tweets_to_consider, 200)

    # Define the tweet fields we want
    fields = "public_metrics,text"

    # Fetch recent tweets from the account using the user ID
    try:
        timeline = client.get_users_tweets(id=account_id, max_results=total_tweets_to_consider, tweet_fields=fields)
    except Exception as e:
        print(f"Error fetching timeline: {e}")
        return []

    # Sort these tweets by engagement (favorites + retweets)
    sorted_tweets = sorted(timeline.data, key=lambda t: t.public_metrics['like_count'] + t.public_metrics['retweet_count'], reverse=True)

    # Extract the tweet texts
    top_tweet_texts = [tweet.text for tweet in sorted_tweets[:num_tweets]]

    return top_tweet_texts



# Async function to generate an image with progress updates
async def generate_image(input_prompt, context, chat_id, message_id, model="dall-e-3", size="1024x1024", quality="standard", filename="generation_times.json"):
    
    print("Generating image Now...")
    attempts = 0
    last_message_content = None

    async def update_progress(start_time, generation_complete):
        
        print("Updating progress...")
        nonlocal last_message_content  # Ensure last_message_content is shared
        avg_time = load_average_generation_time(filename)  # Load average time
        progress_intervals = 15  # Number of progress updates
        for i in range(progress_intervals):
            await asyncio.sleep(avg_time / progress_intervals)  # Wait proportionally based on average time
            if generation_complete.is_set():
                break  # Interrupt progress updates if generation is complete
            elapsed_time = time.time() - start_time
            progress = int((elapsed_time / avg_time) * 100)
            progress = min(progress, 100)  # Cap the progress at 100%
            if attempts == 0:
                progress_message = f"Progress: {progress}%"
            else:
                progress_message = f"Progress: {progress}% (Attempt {attempts + 1}/3)"

            if progress_message != last_message_content:
                try:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=progress_message)
                    last_message_content = progress_message
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=progress_message)
                    last_message_content = progress_message
                except telegram.error.BadRequest as e:
                    if "Message is not modified" in str(e):
                        pass  # Ignore the error if the message is not modified
                    else:
                        raise  # Re-raise the error if it's a different issue


    while attempts < 3:
        start_time = time.time()
        print(start_time)
        
        generation_complete = asyncio.Event()
        print(generation_complete)
        progress_update = asyncio.create_task(update_progress(start_time, generation_complete))

        try:
            print("Generating image...")
            # Generate the image (asynchronously)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: openai_client.images.generate(model=model,prompt=input_prompt, n=1, size=size, quality=quality))

            print("Response received.")  # Debug statement
            print(response)  # Debug: Print the entire response
           
            image_url = response.data[0].url if response.data else None

            print(f"Image URL: {image_url}")  # Debug statement

            generation_complete.set()  # Signal that image generation is complete

            end_time = time.time()

            # Calculate and update the rolling average generation time
            generation_time = end_time - start_time
            update_rolling_average(generation_time, filename, max_entries=10)
            print(generation_time)

            if image_url:
                # Ensure progress updates are interrupted and set progress to 100%
                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Progress: 100%")
                await progress_update  # Await the progress update task to ensure it completes
                return image_url
            else:
                print("Invalid URL: None")
                raise ValueError("Invalid URL: None")

        except openai.BadRequestError as e:
            print(f"OpenAI API Error: {e}")
            attempts += 1
            generation_complete.set()  # Stop the progress updates
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Attempt {attempts}: Failed due to content policy violation. Retrying...")
            await asyncio.sleep(3)  # Pause for 3 seconds
            await progress_update  # Await the progress update task to ensure it completes

            if attempts < 3:
                last_message_content = None  # Reset last_message_content
                continue  # Retry the loop
            else:
                print("Failed after 3 attempts due to content policy violation.")
                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Attempting Final Time with Safer Prompt.")
                safer_prompt = input_prompt + " Please generate an image that is very safe and adheres to content guidelines."
                response = await loop.run_in_executor(None, lambda: openai_client.images.generate(model=model,prompt=safer_prompt, n=1, size=size, quality=quality))
                if not response or not response.data:
                    raise ValueError("Empty or invalid response from API")
                image_url = response.data[0].url
                if image_url:
                    await progress_update  # Await the progress update task to ensure it completes
                    return image_url
                else:
                    raise ValueError("Invalid URL: None")

        except Exception as e:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"An unexpected error occurred: {e}")
            await progress_update  # Await the progress update task to ensure it completes
            break  # Break out of the loop if a non-policy related error occurs

    # Final message after 3 attempts and final safer prompt attempt
    if attempts == 3:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="We Fucked Up, Try Again.")

async def run_bot(context, chat_id):
    initial_message = await context.bot.send_message(chat_id=chat_id, text="Starting the tweet generation process...")
    message_id = initial_message.message_id

    try:
        # Generate a new prompt
        print("Generating new prompt...")
        current_prompt = new_prompt()
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Generated new prompt.")

        # Generate a tweet text using the prompt
        tweet_text = current_prompt
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Generated tweet text: {tweet_text}")

        # Generate an image prompt and an image
        print("Generating image prompt...")
        image_prompt = generate_image_prompt(tweet_text)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Generated image prompt: {image_prompt}")

        print("Generating image...")
        image_url = await generate_image(image_prompt, context, chat_id, message_id)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Generated image URL: {image_url}")

        downloaded_image_path = download_image(image_url)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Downloaded image.")

        # Post the tweet with the image
        tweet_id = post(tweet_text + " $WPC", downloaded_image_path)
        if tweet_id:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Successfully posted tweet with ID: {tweet_id}")
            print(f"Successfully posted tweet with ID: {tweet_id}")
            return tweet_id
        else:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Failed to post tweet.")
            print("Failed to post tweet.")
            return None

    except Exception as e:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"An error occurred: {str(e)}")
        print(f"An error occurred: {e}")
        return None

#THE FOLLOWING FUNCTIONS ARE FOR NFT HYPE POSTS OK THANKS
# Function to select a random image from a folder
folder_path = "NFTDWN"

def select_random_image():
    print ("All images in folder: " + str(os.listdir(folder_path)))
    images = os.listdir(folder_path)
    return random.choice(images)


def generate_message():
    response = openai_client.chat.completions.create(model=ai_model,  # Replace with your model of choice, if different
    messages=[
        {
            "role": "system", 
            "content": large_prompt_1_5
        },
        {
            "role": "user", 
            "content": "In Japanese compose a wild tweet hyping up the FIJI NFTs for World Peace Coin. Mention the NFTs are created by the artists behind Sproto Gremlins. Use lots of emojis! You must keep your tweet under 200 characters."
        }
    ],
    max_tokens=100)
    # In the ChatCompletion response, you access the 'content' of the message directly.
    return response.choices[0].message.content.strip()

def generate_NFT_tweet(): 
    NFT_img_url, image_number = select_random_image()  # Now returns URL and number
    NFT_msg = generate_message()  # Ensure this function returns the message for the tweet
    NFT_img_path = download_image(NFT_img_url)  # Download the image from the URL
    try:
        if NFT_img_path:
            # Upload the media
            media = api.media_upload(NFT_img_path)
            media_id = media.media_id_string
            # Create a tweet with the media
            tweet = client.create_tweet(text=NFT_msg+f" Fiji {image_number} @FijisNFT $WPC", media_ids=[media_id])
        else:
            # If no media_path is provided, just post a text tweet
            tweet = client.create_tweet(text=NFT_msg)

        tweet_id = tweet.data['id']
        return tweet_id

    except TweepyException as error:  
        print(f"Error posting tweet: {error}")
        return None

def select_random_image():
    # Generates a random number between 1 and 3333
    random_number = random.randint(1, 3333)
    # Constructs the URL for the NFT image
    image_url = f"https://fijis.io/image/{random_number}.png"
    return image_url, random_number


def download_image(image_url):
    """ Downloads an image from a URL and returns the local path where it was saved. """
    local_path = "./NFTDWN/temp_image.png"  # Temporary file path for the downloaded image
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(local_path, 'wb') as image_file:
            for chunk in response.iter_content(1024):
                image_file.write(chunk)
        return local_path
    else:
        print("Failed to download image")
        return None

#run_bot();
#generate_NFT_tweet()



