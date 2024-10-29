# run_scraper.py
from token_scraper import PumpTokenScraper
import json

def main():
    # List of tokens you want to scrape
    tokens_to_scrape = [
        "EswvJvhPy8A8rWPdLJ5ATYW6cY5x483oS4QWWroZpump",
        # Add more tokens here
    ]
    
    print("Starting scraper...")
    scraper = PumpTokenScraper(use_headless=True)
    
    try:
        results = scraper.get_multiple_descriptions(tokens_to_scrape)
        
        # Save results to a JSON file
        with open('token_descriptions.json', 'w') as f:
            json.dump(results, f, indent=2)
            
        print("\nResults saved to token_descriptions.json")
        
        # Also print results to console
        for token, info in results.items():
            print(f"\nToken: {token}")
            print(f"Description: {info['description'] if info else 'Not found'}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()