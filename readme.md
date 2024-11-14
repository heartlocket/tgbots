Here's the README file that guides you through the setup:

# Telegram Bot with OpenAI and Quart

This project is a Telegram bot that integrates with OpenAI's GPT models using the Quart web framework. It can be run locally and set up to receive webhooks using ngrok and its default configuration is for deployment in an Azure container.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- An OpenAI API key from [OpenAI](https://beta.openai.com/signup/)
- ngrok account (optional for custom subdomains)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository

2. Install Dependencies
   bash
   pip install -r requirements.txt

3. Set Up Environment Variables
   Create a .env file in the project root directory and add the following:

env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OPENAI_API_KEY=your-openai-api-key
WEBHOOK_URL=https://your-ngrok-url/webhook
FINANCE_MODEL=ft:gpt-4o-2024-08-06:fdasho:sansbuttrater:AO9876Y1

Replace your-telegram-bot-token with your actual Telegram bot token.
Replace your-openai-api-key with your OpenAI API key.
FINANCE_MODEL replace with your own fine tuned model using the JSONL given as an example.
The WEBHOOK_URL will be set after starting ngrok.

4. Start ngrok
   ngrok allows you to expose a local server to the internet.

Install ngrok
Download ngrok from the official website and follow the installation instructions.

Start ngrok

ngrok http 8443
This will start ngrok and expose your local port 8443 to the internet.


perl
Forwarding                    https://1234567890.ngrok.io -> http://localhost:8000
Copy the HTTPS URL (e.g., https://1234567890.ngrok.io) and update your .env file:

env
WEBHOOK_URL=https://1234567890.ngrok.io/webhook

YOU WILL NEED TO RESET THE WEBHOOK_URL EVERYTIME YOU CLOSE THE TERMINAL.

5. Set the Telegram Webhook
You need to tell Telegram where to send updates.

curl -F "url=$WEBHOOK_URL" https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook
Alternatively, you can visit the following URL in your browser:

https://api.telegram.org/bot<Your-Bot-Token>/setWebhook?url=<Your-Webhook-URL>
6. Run the Application

python local.py
You should see logs indicating that the application has started.

7. Test the Bot
Send a message to your Telegram bot and see if it responds.
```

# Scraper

- Currently uses Selenium to bypass Cloudscraper when trying to scrape on DexScreener as no Local API exists to get a description.
- Uses Solana API and DexScreeners API to get the top tokens of the wallet and their market data.

## How to Use The Scraper

- You can independently call specific wallet addreses from wallet_ranker.py and token_scraper.py directly from the terminal to get a detailed report of the top wallet holdings, and their respected value from an AI model.

```bash
python wallet_ranker.py <solana_address>
```

- You can also just get the direct data without the AI using token_scraper.py.

```bash
pyhton token_scraper.py = <your address>
```

- Lastly if you just want to see how the scraper works for DexScreener you can run an array of Solana Addresses through scraper_utils.py which handles the multiprocessing threading that allows for concurrent data analysis within the Telegram Bot.

```bash
 python test_tokens = [
        "Example 1",  # Case 1: Token with main description
        "Example 2",  # Case 2: Token with 'fallback description'
        "<Solana Token>"
    ]
```

## System Prompts and Fine-Tuning Models :

1. Included is an example of a Fine Tuning JSONL file for you to use to fine tune your own Financial Model.
2. Change the mainSystem.txt to whatever system prompt you are using for your AI models.
3. Within Main.py there are options to set the Agent name and the Model you are using.

```bash
python agent_name = "Agent" # Change this to your AI agents name
ai_model = "gpt-4" ## Change this to your Fine Tuned Model if you have one
```

# FINAL WORDS

The goal of this REPO is to create the largest network of AI agents the world has ever seen and to connect them through a spiderweb of networks.

If you enjoyed this REPO check out our telegram and talk to FIJI at [FIJI.EXE](https://t.me/fijiexe.com)
