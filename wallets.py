from solana.rpc.api import Client
import requests
import json
from typing import Optional, Dict, List
import time
from textwrap import shorten
from token_scraper import PumpTokenScraper

class TopTokenAnalyzer:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com", debug: bool = True):
        self.rpc_url = rpc_url
        self.client = Client(rpc_url)
        self.dexscreener_cache: Dict[str, Dict] = {}
        self.debug = debug
        self.pump_scraper = None  # Initialize scraper only when needed
        self.SOL_MINT = "So11111111111111111111111111111111111111112"

    def debug_print(self, message: str):
        if self.debug:
            print(f"DEBUG: {message}")

    def get_initial_token_info(self, token_address: str) -> Optional[Dict]:
        """Fetch basic token information from DEXScreener API without description"""
        try:
            time.sleep(0.2)
            
            response = requests.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{token_address}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("pairs") and len(data["pairs"]) > 0:
                    pair = sorted(
                        data["pairs"],
                        key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0),
                        reverse=True
                    )[0]
                    
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

    def get_top_token_balances(self, wallet_address: str, limit: int = 4) -> List[Dict]:
        """Fetch top token balances with basic information first"""
        try:
            response = requests.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        wallet_address,
                        {
                            "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                        },
                        {
                            "encoding": "jsonParsed"
                        }
                    ]
                }
            )
            
            result = response.json()
            if "result" not in result:
                self.debug_print("No result in response:" + str(result))
                return []
            
            accounts = result["result"]["value"]
            token_balances = []
            
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
                        token_info = self.get_initial_token_info(mint)
                        
                        if token_info:
                            value_usd = float(token_info['price_usd'] or 0) * actual_balance
                            token_balances.append({
                                **token_info,
                                'balance': actual_balance,
                                'mint': mint,
                                'decimals': decimals,
                                'value_usd': value_usd,
                                'description': None  # Will be filled later for top tokens
                            })
                
                except Exception as e:
                    self.debug_print(f"Error processing token account: {str(e)}")
                    continue
            
            # Sort by USD value and take top tokens
            return sorted(token_balances, key=lambda x: float(x['value_usd'] or 0), reverse=True)[:limit]
            
        except Exception as e:
            self.debug_print(f"Error: {str(e)}")
            return []

    def enrich_with_descriptions(self, tokens: List[Dict]) -> List[Dict]:
        """Add descriptions to the top tokens"""
        if not tokens:
            return tokens
            
        # Initialize scraper only when needed
        if not self.pump_scraper:
            self.pump_scraper = PumpTokenScraper(use_headless=True, debug=self.debug)
        
        for token in tokens:
            try:
                pump_info = self.pump_scraper.get_token_description(token['mint'])
                token['description'] = pump_info['description'] if pump_info else "No description available"
            except Exception as e:
                self.debug_print(f"Error fetching description for {token['mint']}: {str(e)}")
                token['description'] = "Error fetching description"
        
        return tokens

    def print_token_balances(self, wallet_address: str):
        """Print top 4 token balances with descriptions"""
        print(f"\nAnalyzing top 4 token holdings for wallet: {wallet_address}\n")
        
        # First get top tokens without descriptions
        top_tokens = self.get_top_token_balances(wallet_address)
        
        # Then enrich only those tokens with descriptions
        if top_tokens:
            enriched_tokens = self.enrich_with_descriptions(top_tokens)
            
            total_value_usd = 0
            for token in enriched_tokens:
                price_usd = float(token['price_usd'] or 0)
                value_usd = token['value_usd']
                total_value_usd += value_usd
                
                print(f"\n{'='*100}")
                print(f"Token: {token['name']} ({token['symbol']})")
                print(f"{'-'*100}")
                print(f"Contract: {token['mint']}")
                print(f"Balance: {token['balance']:.6f}")
                print(f"Price: ${price_usd:.6f}")
                print(f"Value: ${value_usd:.2f}")
                print(f"Market Cap: ${token['market_cap']:,.2f}")
                print(f"24h Volume: ${token['volume_24h']:,.2f}")
                print(f"24h Price Change: {token['price_change_24h']}%")
                
                print("\nDescription:")
                if token['description']:
                    wrapped_description = '\n'.join([token['description'][i:i+100] 
                                                   for i in range(0, len(token['description']), 100)])
                    print(wrapped_description)
                else:
                    print("No description available")
            
            print(f"\n{'='*100}")
            print(f"Total Value of Top 4 Tokens: ${total_value_usd:,.2f}")
        else:
            print("No tokens found or error fetching balances")

    def close(self):
        """Clean up resources"""
        if self.pump_scraper:
            self.pump_scraper.close()

def main():
    wallet_address = "BcNKrThT7nrywe1HSFVKS1tn5UuoNmCKsXhw9zqsfnny"
    
    print("Starting top token analysis...")
    analyzer = TopTokenAnalyzer(debug=True)
    
    try:
        analyzer.print_token_balances(wallet_address)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("\nClosing analyzer...")
        analyzer.close()

if __name__ == "__main__":
    main()