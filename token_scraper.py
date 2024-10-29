# token_scraper.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class PumpTokenScraper:
    def __init__(self, use_headless: bool = True, debug: bool = True):
        """Initialize the scraper with optional headless mode and debugging"""
        self.debug = debug
        chrome_options = Options()
        if use_headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--enable-javascript')
        
        if self.debug:
            print("Initializing Chrome WebDriver...")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def debug_print(self, message: str):
        """Print debug messages if debug mode is enabled"""
        if self.debug:
            print(f"DEBUG: {message}")

    def get_token_description(self, token_address: str) -> dict:
        """Scrape token description with enhanced error handling and debugging"""
        try:
            url = f"https://pump.fun/{token_address}"
            self.debug_print(f"Navigating to {url}")
            self.driver.get(url)
            
            # Wait for initial page load
            self.debug_print("Waiting for page load...")
            time.sleep(5)  # Give JavaScript more time to render
            
            # Output page title and URL to verify we're on the right page
            self.debug_print(f"Current URL: {self.driver.current_url}")
            self.debug_print(f"Page title: {self.driver.title}")
            
            # Try to find the description with multiple selectors
            wait = WebDriverWait(self.driver, 15)
            description = None
            
            # First try break-anywhere class
            try:
                self.debug_print("Trying to find element with break-anywhere class...")
                description_element = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "break-anywhere"))
                )
                description = description_element.text
                self.debug_print(f"Found description: {description}")
            except TimeoutException:
                self.debug_print("Could not find break-anywhere class, trying alternative selectors...")
                
                # Try alternative selectors
                selectors = [
                    "//div[contains(@class, 'text-xs') and contains(@class, 'text-gray-400')]",
                    "//div[contains(text(), 'Description')]//following-sibling::div",
                    "//div[contains(@class, 'text-gray-400')]"
                ]
                
                for selector in selectors:
                    try:
                        self.debug_print(f"Trying selector: {selector}")
                        element = wait.until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        description = element.text
                        if description:
                            self.debug_print(f"Found description using alternative selector: {description}")
                            break
                    except:
                        continue

            if not description:
                self.debug_print("Could not find description with any selector")
                # Dump page source for debugging
                with open('page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.debug_print("Page source saved to page_source.html")
                return None

            return {
                'token_address': token_address,
                'description': description
            }
            
        except Exception as e:
            self.debug_print(f"Error: {str(e)}")
            # Save screenshot for debugging
            self.driver.save_screenshot('error_screenshot.png')
            self.debug_print("Error screenshot saved as error_screenshot.png")
            return None

    def get_multiple_descriptions(self, token_addresses: list) -> dict:
        """Fetch descriptions for multiple tokens"""
        results = {}
        for address in token_addresses:
            info = self.get_token_description(address)
            if info:
                results[address] = info
            time.sleep(2)  # Be nice to the server
        return results

    def close(self):
        """Clean up resources"""
        if self.debug:
            print("Closing WebDriver...")
        self.driver.quit()

# Create a simple test script
if __name__ == "__main__":
    # Test token addresses
    test_tokens = [
        "EswvJvhPy8A8rWPdLJ5ATYW6cY5x483oS4QWWroZpump",
    ]
    
    print("Starting token description scraper...")
    scraper = PumpTokenScraper(use_headless=True)
    
    try:
        for token in test_tokens:
            print(f"\nFetching info for token: {token}")
            info = scraper.get_token_description(token)
            if info:
                print("Found information:")
                print(json.dumps(info, indent=2))
            else:
                print("Failed to fetch token info")
            time.sleep(2)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("\nClosing scraper...")
        scraper.close()