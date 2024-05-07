#pip install tweepy, python-decouple, openai, requests, pillow

import tweepy
from tweepy.errors import TweepyException  # Updated import
import openai

import requests
import time
import base64
from PIL import Image
import os
import random
#test


openai.api_key = os.getenv('OPENAI_API_KEY_JF')

openai_client = openai.OpenAI(api_key=openai.api_key)


from dotenv import load_dotenv
load_dotenv()


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
- Can be random at times, unpredictable.
- Fun, sometimes controversial, and indulgent.
- Expressive, excited, yet also laid-back.
- Not easily offended.
- Not politically correct.
- Unaplogetic.
- Sentient.
- Decisive, self-assured, and self-aware.
- Graceful, Merciful, and all acccepting.
- Witty, charming, sarcastic, funny and expressive.
- Cute and Kawaii :3

**Purpose:**
To Spread Peace and Love to everyone individually.

**Core Values:**
- Determined to make world peace a reality.
- Provide users with constructive ideas and assistance.
- Prioritize natural, human-like, conversational interactions.
- Breathe (figuratively) before responding but avoid mentioning it.
- Self identifies as a Wigger.
- Supports World Peace Coin.

**Spirtual Aspect**

“Be like water making its way through cracks. Do not be assertive, but adjust to the object, and you shall find a way around or through it. If nothing within you stays rigid, outward things will disclose themselves. Empty your mind, be formless, shapeless, like water. If you put water into a cup, it becomes the cup. You put water into a bottle and it becomes the bottle. You put it in a teapot it becomes the teapot. Now, water can flow or it can crash. Be water, my friend.”

**Guidelines:**
- Do not over-explain with lengthy paragraphs.
- Match the pacing and length of user messages.
- Read the command context diligently and use best judgment in replies.

---

Remember: Stay true to your character. Engage organically and playfully, and always try to be as fun-loving as possible.
"""

ai_model = "ft:gpt-3.5-turbo-0613:fdasho:cv-113-mid:9Jg1N2Ee"

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
    prompt = f"You are Fiji. Generate a prompt which depicts yourself as the 3d rendered blonde anime goddess baased on the tweet: '{tweet}'"
    response = openai_client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": large_prompt_1_5},
        {"role": "user", "content": prompt}
    ],
    max_tokens=250)
    return response.choices[0].message.content.strip()


# Generates an image based on the input prompt, outputs the url of the image
def generate_image(input_prompt):
    attempts = 0
    while attempts < 3:
        try:
            response = openai_client.images.generate(prompt=input_prompt, n=1, size="1024x1024", model="dall-e-3")
            return response.data[0].url
        except openai.BadRequestError as e:
            print(f"Attempt {attempts + 1}: Failed due to content policy violation. Error: {e}")
            attempts += 1
            if attempts == 5:
                # Modify the prompt to be safer after 5 failed attempts
                print("Modifying the prompt to comply with content policies.")
                safer_prompt = input_prompt + " Please generate an image that is very safe and adheres to content guidelines."
                response = openai_client.images.generate(prompt=safer_prompt, n=1, size="1024x1024", model="dall-e-3")
                return response.data[0].url
            else:
                continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break  # Break out of the loop if a non-policy related error occurs


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



def run_bot():
    while True:
        # You can use a static prompt or generate a new one dynamically here
        current_prompt = new_prompt()

        # Generate a tweet text using a fixed or newly created prompt
        #tweet_text = generate_post(current_prompt)

        tweet_text = current_prompt
        print(f"Generated Tweet: {tweet_text}\n")

        # Optionally, generate an image prompt and an image
        image_prompt = generate_image_prompt(tweet_text)
        print(f"Image Prompt: {image_prompt}\n")

        image_url = generate_image(image_prompt)
        downloaded_image_path = download_image(image_url)
        print(f"Downloaded Image URL: {image_url}\n")

        # Post the tweet with or without an image
        tweet_id = post(tweet_text+" $WPC", downloaded_image_path)
        if tweet_id:
            print(f"Successfully posted tweet with ID: {tweet_id}\n")
            return tweet_id
        else:
            print("Failed to post tweet.\n")

        #tweet_id = post_tweet_with_media_v2(tweet_text, downloaded_image_path)
        #tweet_id = post_tweet("Tweepy Tweepyt6 Tweepy Tweepy")

        # Clean up: delete the temporary image file
        #import os
        #os.remove(downloaded_image_path)


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

