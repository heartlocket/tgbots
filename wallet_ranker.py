import asyncio
import json
import logging
import os
import sys
import re
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
from token_scraper import TopTokenAnalyzer

# -----------------------------
# Configuration and Setup
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

## CHANGE THIS PART LATER TO MORE SECURELY STORE THE SYSTEM PROMPT & OPEN SOURCE

try:
    with open('mainSystem.txt', 'r', encoding='utf-8') as file:
        fiji_system = file.read()
except Exception as e:
    logger.error(f"Error reading mainSystem.txt: {e}")
    sys.exit(1)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

FINANCE_MODEL = os.getenv('FINANCE_MODEL')

MODELS = {
    'FINANCE_MODEL': "ft:gpt-4o-2024-08-06:fdasho:sansbuttrater:AO9876Y1"
}


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def generate_chat_completion(self, model: str, prompt: str, max_tokens: int = 150, system_message: str = "You are a helpful assistant that analyzes cryptocurrency tokens.") -> str:
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.5,
                frequency_penalty=0.5,
                presence_penalty=0.6
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error in analysis: {str(e)}"

class WalletRanker:
    def __init__(self):
        self.openai_client = OpenAIClient()

    def generate_ranking_prompt(self, tokens_data: List[Dict]) -> str:
        tokens_json = json.dumps(tokens_data, indent=2)
        return (
            "Given the following list of tokens, analyze each token individually "
            "and provide scores for the metrics below. Do not rank them.\n\n"
            f"Token data:\n{tokens_json}\n\n"
            "For each token, provide scores on a scale of 1-10 in this exact format:\n\n"
            "TOKEN: [Token Name] ([Symbol])\n"
            "KEK (FUNNY): [Score/10]\n"
            "AWW (CUTE): [Score/10]\n"
            "RETARD (HIGH IQ): [Score/10]\n"
            "REDDITOR (LOW IQ): [Score/10]\n"
            "SWAG INDEX: [Score/10]\n"
            "BRIEF COMMENT: [One-line analysis]\n"
            "---\n\n"
            "Please analyze each token separately using the format above.\n"
            "Maintain consistent scoring across all tokens.\n"
            "Be genuine and entertaining in your scoring."
        )

    def format_analysis(self, analysis: str, tokens: List[Dict]) -> str:
        """
        Add Telegram-specific formatting with emojis, metrics, and links
        Using Telegram's HTML formatting for better copy-paste support
        """
        try:
            token_blocks = re.split(r'---', analysis.strip())
            formatted_blocks = []
            
            for block, token_data in zip(token_blocks, tokens):
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                token_header = lines[0].strip()
                mint_address = token_data['mint']
                dexscreener_url = f"https://dexscreener.com/solana/{mint_address}"
                
                # Using HTML formatting for better copy support
                formatted_block = (
                    f"🌟 <b>{token_header}</b>\n\n"
                    f"📋 <code>{mint_address}</code>\n"
                    f"🔍 <a href='{dexscreener_url}'>View on DexScreener</a>\n\n"
                    f"💰 Value: ${float(token_data['value_usd']):,.2f}\n"
                    f"📊 Price: ${float(token_data['price_usd']):,.6f}\n"
                    f"📈 24h Change: {token_data['price_change_24h']}%\n"
                    f"💎 Market Cap: ${float(token_data['market_cap']):,.2f}\n"
                    f"💫 Balance: {token_data['balance']:.4f}\n\n"
                    f"<b>Analysis:</b>\n"
                )
                
                # Add AI analysis with emojis
                for line in lines[1:]:
                    formatted_line = line.strip()
                    if 'KEK' in formatted_line:
                        formatted_block += f"😂 {formatted_line}\n"
                    elif 'AWW' in formatted_line:
                        formatted_block += f"🐶 {formatted_line}\n"
                    elif 'RETARD' in formatted_line:
                        formatted_block += f"🧠 {formatted_line}\n"
                    elif 'REDDITOR' in formatted_line:
                        formatted_block += f"🤡 {formatted_line}\n"
                    elif 'SWAG INDEX' in formatted_line:
                        formatted_block += f"🚀 {formatted_line}\n"
                    elif 'BRIEF COMMENT' in formatted_line:
                        formatted_block += f"💬 {formatted_line}\n"
                    else:
                        formatted_block += f"{formatted_line}\n"
                
                formatted_blocks.append(formatted_block)

            total_value = sum(float(t['value_usd']) for t in tokens)
            final_summary = f"\n🏦 <b>Total Portfolio Value:</b> ${total_value:,.2f}"
            
            # Add divider between tokens
            divider = "\n" + "═" * 35 + "\n"
            
            return divider.join(formatted_blocks) + final_summary

        except Exception as e:
            logger.error(f"Error formatting analysis: {e}")
            return analysis  # Fallback to raw analysis if formatting fails

    async def analyze_wallet(self, wallet_address: str) -> str:
        logger.info(f"Analyzing wallet: {wallet_address}")
        analyzer = TopTokenAnalyzer(debug=False)
        try:
            tokens = await analyzer.get_token_data(wallet_address)
            if not tokens:
                return "No token data found for the provided wallet address"

            prompt = self.generate_ranking_prompt(tokens)
            FINANCE_MODEL = await self.openai_client.generate_chat_completion(
                MODELS['FINANCE_MODEL'],
                prompt,
                max_tokens=1000,
                system_message="You are an AI model trained to rank cryptocurrency tokens based on their fundamentals and market data."
            )

            logger.info("Analysis complete")
            return self.format_analysis(FINANCE_MODEL, tokens)

        except Exception as e:
            logger.error(f"Error in analyze_wallet: {e}")
            return f"Error analyzing wallet: {str(e)}"

        finally:
            await analyzer.close()  # Ensure proper resource cleanup


async def main():
    if len(sys.argv) != 2:
        print("Usage: python wallet_ranker.py <SOLANA_WALLET_ADDRESS>")
        sys.exit(1)

    wallet_address = sys.argv[1]
    ranker = WalletRanker()
    result = await ranker.analyze_wallet(wallet_address)
    print("\nAnalysis Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())