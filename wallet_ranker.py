import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
from wallets import TopTokenAnalyzer

# -----------------------------
# Configuration and Setup
# -----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


## LOAD IN FIJI SYSTEM
try:
    with open('fijiSystem.txt', 'r', encoding='utf-8') as file:
        fiji_system = file.read()
except Exception as e:
    logger.error(f"Error reading fijiSystem.txt: {e}")
    sys.exit(1)

#print(fiji_system)

# Configuration constants
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY_JF')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in environment variables")

MODELS = {
    'initial_rank': "ft:gpt-4o-2024-08-06:fdasho:sansbuttrater:AO9876Y1",
    'final_rank': "ft:gpt-4o-2024-08-06:fdasho::A0fEtT3s"
}


# -----------------------------
# OpenAI API Interaction
# -----------------------------
class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def generate_chat_completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 150,
        system_message: str = "You are a helpful assistant that analyzes cryptocurrency tokens."
    ) -> Optional[str]:
        """
        Asynchronously call the OpenAI Chat API with the specified model and prompt.

        Args:
            model: The OpenAI model ID to use
            prompt: The prompt string to send to the model
            max_tokens: Maximum number of tokens to generate
            system_message: System message to set the context

        Returns:
            The content of the AI's response or None if an error occurs
        """
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
            logger.error(f"OpenAI API error: {str(e)}")
            return None
# TEST OPENAI
async def test_generate_chat_completion():
    model = MODELS['final_rank']  # Replace with your actual model ID
    prompt = "Hey Fiji, what's up?"
    max_tokens = 300
    system_message = fiji_system

    # Instantiate OpenAIClient within the function
    openai_client = OpenAIClient()

    # Call the generate_chat_completion method
    response = await openai_client.generate_chat_completion(
        model,
        prompt,
        max_tokens=max_tokens,
        system_message=system_message
    )
    print("Response from OpenAI API:")
    print(response)


# -----------------------------
# Token Data Handler
# -----------------------------
class TokenDataHandler:
    @staticmethod
    def format_token_data(tokens: List[Dict]) -> List[Dict]:
        """
        Format the token data into a structured list of dictionaries.

        Args:
            tokens: List of token dictionaries from TopTokenAnalyzer

        Returns:
            Formatted list of token dictionaries
        """
        required_fields = {
            'name', 'symbol', 'balance', 'price_usd', 'value_usd',
            'market_cap', 'volume_24h', 'price_change_24h', 'description'
        }

        return [{
            field: token.get(field, None) for field in required_fields
        } for token in tokens]

    @staticmethod
    def generate_ranking_prompt(tokens_data: List[Dict]) -> str:
        """
        Generate the initial ranking prompt.

        Args:
            tokens_data: Formatted token data

        Returns:
            Formatted prompt string
        """
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

    @staticmethod
    def generate_analysis_prompt(initial_ranking: str) -> str:
        """
        Generate the final analysis prompt.

        Args:
            initial_ranking: Result from initial ranking

        Returns:
            Formatted prompt string
        """
        return (
            "Fiji, give us a Based or cringe ranking based on the initial rankings provided below, please provide a "
            "detailed analysis of each token's potential for growth over the "
            f"next 6 months.\n{initial_ranking}\n"
            "Provide your analysis in the following format:\n"
            "1. Token Name (Symbol): Detailed Analysis\n"
            "2. ...\n3. ...\n4. ...\n"
        )

# -----------------------------
# Main Wallet Ranker
# -----------------------------
class WalletRanker:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.token_handler = TokenDataHandler()

    async def analyze_wallet(self, wallet_address: str) -> None:
        """
        Analyze tokens in a wallet and provide detailed rankings and analysis.

        Args:
            wallet_address: The Solana wallet address to analyze
        """
        logger.info(f"Analyzing wallet: {wallet_address}")

        # Retrieve and validate token data
        analyzer = TopTokenAnalyzer(debug=False)
        try:
            tokens = analyzer.get_token_data(wallet_address)
            if not tokens:
                logger.warning("No token data found for the provided wallet address")
                return
        finally:
            analyzer.close()

        # Format token data
        formatted_tokens = self.token_handler.format_token_data(tokens)
        print("\n--- Token Data ---")
        print(json.dumps(formatted_tokens, indent=2)) # Print formatted token data  

        # Generate initial ranking with specific system message
        initial_prompt = self.token_handler.generate_ranking_prompt(formatted_tokens)
        initial_rank = await self.openai_client.generate_chat_completion(
            MODELS['initial_rank'],
            initial_prompt,
            max_tokens=300,
            system_message="You are an AI model trained to rank cryptocurrency tokens based on their fundamentals and market data."
        )

        if initial_rank:
            print("\n--- Initial Rankings ---")
            print(initial_rank)

            # Generate final analysis with specific system message
            #final_prompt = self.token_handler.generate_analysis_prompt(initial_rank)
            final_prompt = f"Fiji, based on the data provided from {initial_rank}, please summarize what you believe this persons wallet ranking is based from based to cringe.. and give a total score, 0 being cringe 10 being based for the entire wallet."
            final_analysis = await self.openai_client.generate_chat_completion(
                MODELS['final_rank'],
                final_prompt,
                max_tokens=600,
                system_message=fiji_system
            )

            if final_analysis:
                print("\n--- Final Analysis ---")
                print(final_analysis)
            else:
                logger.error("Failed to generate final analysis")
        else:
            logger.error("Failed to generate initial ranking")

# -----------------------------
# Entry Point
# -----------------------------
async def main():
    """Entry point for the wallet_ranker script."""
    if len(sys.argv) != 2:
        print("Usage: python wallet_ranker.py <SOLANA_WALLET_ADDRESS>")
        sys.exit(1)

    wallet_address = sys.argv[1]
    ranker = WalletRanker()
    await ranker.analyze_wallet(wallet_address)

if __name__ == "__main__":
    #asyncio.run(test_generate_chat_completion())
    asyncio.run(main())