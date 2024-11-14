import asyncio
from solana.rpc.api import Client
import aiohttp
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor
from scraper_utils import run_scrapers


class TopTokenAnalyzer:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com", debug: bool = True):
        self.rpc_url = rpc_url
        self.client = Client(rpc_url)
        self.debug = debug
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.thread_pool = ThreadPoolExecutor(max_workers=16)  # Increased parallelism
        self.session = None  # Reused aiohttp session

    async def initialize_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    def debug_print(self, message: str):
        if self.debug:
            print(f"DEBUG: {message}")

    async def get_initial_token_info(self, token_address: str) -> Optional[Dict]:
        try:
            async with self.session.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("pairs"):
                        pair = max(
                            data["pairs"],
                            key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0)
                        )

                        self.debug_print(f"Pair data: {pair['baseToken']['symbol']}")

                        return {
                            'symbol': pair["baseToken"]["symbol"],
                            'name': pair["baseToken"]["name"],
                            'price_usd': pair.get("priceUsd", "0"),
                            'market_cap': pair.get("marketCap", 0),
                            'volume_24h': pair.get("volume", {}).get("h24", 0),
                            'price_change_24h': pair.get("priceChange", {}).get("h24", 0)
                        }
                   
            return None
        except Exception as e:
            self.debug_print(f"Error fetching DEXScreener data for {token_address}: {str(e)}")
            return None

    async def get_top_token_balances(self, wallet_address: str, limit: int = 4) -> List[Dict]:
        try:
            await self.initialize_session()
            async with self.session.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        wallet_address,
                        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                        {"encoding": "jsonParsed"}
                    ]
                },
                timeout=10
            ) as response:
                result = await response.json()
                accounts = result.get("result", {}).get("value", [])

                tasks, mints_balances = [], []
                for account in accounts:
                    try:
                        parsed_data = account["account"]["data"]["parsed"]["info"]
                        mint = parsed_data["mint"]
                        if mint == self.SOL_MINT:
                            continue

                        amount = int(parsed_data["tokenAmount"]["amount"])
                        decimals = parsed_data["tokenAmount"]["decimals"]
                        actual_balance = float(amount) / (10 ** decimals)

                        if actual_balance > 0:
                            tasks.append(self.get_initial_token_info(mint))
                            mints_balances.append((mint, actual_balance, decimals))
                    except Exception as e:
                        self.debug_print(f"Error processing token account: {str(e)}")

                token_infos = await asyncio.gather(*tasks, return_exceptions=True)
                token_balances = []
                for token_info, (mint, actual_balance, decimals) in zip(token_infos, mints_balances):
                    self.debug_print(f"Token info: {token_info}")
                    if isinstance(token_info, Exception) or token_info is None:
                        continue
                    try:
                        value_usd = float(token_info['price_usd'] or 0) * actual_balance
                        token_balances.append({
                            **token_info,
                            'balance': actual_balance,
                            'mint': mint,
                            'decimals': decimals,
                            'value_usd': value_usd,
                            'description': None
                        })
                    except Exception as e:
                        self.debug_print(f"Error constructing token balance: {str(e)}")

                return sorted(token_balances, key=lambda x: x['value_usd'], reverse=True)[:limit]
        except Exception as e:
            self.debug_print(f"Error in get_top_token_balances: {str(e)}")
            return []

    async def get_token_data(self, wallet_address: str) -> List[Dict]:
        try:
            tokens = await self.get_top_token_balances(wallet_address)
            if not tokens:
                return []

            mints = [token['mint'] for token in tokens]
            loop = asyncio.get_running_loop()
            scraping_results = await loop.run_in_executor(self.thread_pool, run_scrapers, mints)

            for token in tokens:
                result = next((desc for mint, desc in scraping_results if mint == token['mint']), "No description")
                token['description'] = result

            return tokens
        except Exception as e:
            self.debug_print(f"Error in get_token_data: {e}")
            return []

    async def print_token_balances(self, wallet_address: str):
        print(f"\nAnalyzing top 4 token holdings for wallet: {wallet_address}\n")

        tokens = await self.get_token_data(wallet_address)
        if not tokens:
            print("No tokens found or error fetching balances")
            return

        total_value_usd = sum(float(token['value_usd'] or 0) for token in tokens)
        for token in tokens:
          try:
              price_usd = float(token['price_usd'] or 0)
              value_usd = float(token['value_usd'] or 0)
              
              print(f"\n{'='*100}")
              print(f"Token: {token['name']} ({token['symbol']})")
              print(f"{'-'*100}")
              print(f"Contract: {token['mint']}")
              print(f"Balance: {token['balance']:.6f}")
              print(f"Price: ${price_usd:.6f}")
              print(f"Value: ${value_usd:.2f}")
              print(f"Market Cap: ${float(token['market_cap']):,.2f}")
              print(f"24h Volume: ${float(token['volume_24h']):,.2f}")
              print(f"24h Price Change: {token['price_change_24h']}%")
              print(f"\nDescription:\n{token['description']}")
          except Exception as e:
              print(f"Error printing token details: {e}")
        print(f"\n{'='*100}")
        print(f"Total Value of Top 4 Tokens: ${total_value_usd:,.2f}")

    async def close(self):
      await self.close_session()
      self.debug_print("Resources have been cleaned up.")

# Entry point
async def main():
    wallet_address = "BcNKrThT7nrywe1HSFVKS1tn5UuoNmCKsXhw9zqsfnny"
    analyzer = TopTokenAnalyzer(debug=True)
    try:
        await analyzer.print_token_balances(wallet_address)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main())