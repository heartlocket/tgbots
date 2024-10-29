from solana.rpc.api import Client
import requests
import json
from typing import Optional, Dict, List
import time
from textwrap import shorten
from token_scraper import PumpTokenScraper  # Our previous scraper for pump.fun

class EnhancedTokenAnalyzer:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com", debug: bool = True):
        self.rpc_url = rpc_url
        self.client = Client(rpc_url)
        self.dexscreener_cache: Dict[str, Dict] = {}
        self.debug = debug
        self.pump_scraper = PumpTokenScraper(use_headless=True, debug=debug)

    def debug_print(self, message: str):
        if self.debug:
            print(f"DEBUG: {message}")

    def get_token_info_from_dexscreener(self, token_address: str) -> Optional[Dict]:
        """Fetch token information from DEXScreener API with rate limiting"""
        if token_address in self.dexscreener_cache:
            return self.dexscreener_cache[token_address]
        
        try:
            time.sleep(0.2)  # Rate limiting
            
            response = requests.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{token_address}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("pairs") and len(data["pairs"]) > 0:
                    pair = data["pairs"][0]
                    
                    # Get description from pump.fun
                    pump_info = self.pump_scraper.get_token_description(token_address)
                    
                    token_info = {
                        'symbol': pair["baseToken"]["symbol"],
                        'name': pair["baseToken"]["name"],
                        'price_usd': pair.get("priceUsd", "0"),
                        'market_cap': pair.get("marketCap", 0),
                        'description': pump_info['description'] if pump_info else "No description available"
                    }
                    self.dexscreener_cache[token_address] = token_info
                    return token_info
            
            return None
        except Exception as e:
            self.debug_print(f"Error fetching DEXScreener data for {token_address}: {str(e)}")
            return None

    def get_token_balances(self, wallet_address: str) -> List[Dict]:
        """Fetch all token balances and their information"""
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
                    amount = int(parsed_data["tokenAmount"]["amount"])
                    decimals = parsed_data["tokenAmount"]["decimals"]
                    
                    actual_balance = float(amount) / (10 ** decimals)
                    
                    if actual_balance > 0:  # Only include non-zero balances
                        self.debug_print(f"Processing token: {mint}")
                        
                        # Get token info from DEXScreener
                        token_info = self.get_token_info_from_dexscreener(mint)
                        
                        if token_info:
                            value_usd = float(token_info['price_usd'] or 0) * actual_balance
                            token_balances.append({
                                'symbol': token_info['symbol'],
                                'name': token_info['name'],
                                'balance': actual_balance,
                                'mint': mint,
                                'decimals': decimals,
                                'price_usd': token_info['price_usd'],
                                'value_usd': value_usd,
                                'market_cap': token_info['market_cap'],
                                'description': token_info['description']
                            })
                        else:
                            token_balances.append({
                                'symbol': 'UNKNOWN',
                                'name': f'Token ({mint[:8]}...)',
                                'balance': actual_balance,
                                'mint': mint,
                                'decimals': decimals,
                                'price_usd': '0',
                                'value_usd': 0,
                                'market_cap': 0,
                                'description': "Token not found"
                            })
                
                except Exception as e:
                    self.debug_print(f"Error processing token account: {str(e)}")
                    continue
            
            return sorted(token_balances, key=lambda x: float(x['value_usd'] or 0), reverse=True)
            
        except Exception as e:
            self.debug_print(f"Error: {str(e)}")
            return []

    def print_token_balances(self, wallet_address: str):
        """Print all token balances in a formatted way"""
        print(f"\nAnalyzing wallet: {wallet_address}\n")
        balances = self.get_token_balances(wallet_address)
        
        if balances:
            total_value_usd = 0
            for token in balances:
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
                
                print("\nDescription:")
                description = token['description']
                wrapped_description = '\n'.join([description[i:i+100] for i in range(0, len(description), 100)])
                print(wrapped_description)
            
            print(f"\n{'='*100}")
            print(f"Total Portfolio Value: ${total_value_usd:,.2f}")
        else:
            print("No tokens found or error fetching balances")

    def close(self):
        """Clean up resources"""
        self.pump_scraper.close()

def main():
    wallet_address = "7Cy4c5eNE6Livc2AHbi1ELhG7Xm4At2bNLnuwsFEQRgT"
    
    print("Starting enhanced token analysis...")
    analyzer = EnhancedTokenAnalyzer(debug=True)
    
    try:
        analyzer.print_token_balances(wallet_address)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("\nClosing analyzer...")
        analyzer.close()

if __name__ == "__main__":
    main()