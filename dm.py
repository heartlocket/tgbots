from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
try:
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY_JF_2"),
    )
    print("OpenAI client successfully initialized.")

    # Attempt to create a new image
    print("Generating image...")
    response = client.images.generate(
        model="dall-e-3",
        prompt="Create a 3D render of a blonde anime goddess with long golden hair, dressed in a pink suit of armor. She's positioned within an expansive digital financial chart, not a physical space. The focus is on her interaction with a large, digital red 'candlestick' bar from the chart, symbolizing a significant market downturn. This candlestick bar is not a physical object but a part of the digital chart display. The goddess is in a squatting position, performing an overhead press, using her strength to hold up this digital red candlestick bar and prevent it from falling further in the chart. Her arms are extended upwards, muscles visibly strained, emphasizing that she is interacting with a digital element, not a physical candle.",
        size="1024x1024",
        quality="hd",
        n=1,
    )

    # Extract and print the image URL
    image_url = response.data[0].url
    print(f"Image successfully generated: {image_url}")

except Exception as e:
    # Print any errors that occur
    print(f"An error occurred: {e}")
