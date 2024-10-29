import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

class PumpTokenScraper:
    def __init__(self, use_headless: bool = True, debug: bool = True):
        self.debug = debug
        chrome_options = Options()
        if use_headless:
            chrome_options.add_argument('--headless=new')
        
        # Enhanced options for better JavaScript execution
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--window-size=1920,1080")
        
        if self.debug:
            print("Initializing Chrome WebDriver...")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(20)
        self.description_cache = {}

    def wait_for_page_load(self):
        """Wait for the page to be fully loaded"""
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # Additional small delay to ensure JavaScript execution
            time.sleep(1)
        except:
            pass

    def get_token_description(self, token_address: str) -> dict:
        """Enhanced token description scraping with better error handling"""
        if token_address in self.description_cache:
            return self.description_cache[token_address]

        if self.debug:
            print(f"\nFetching description for {token_address}")

        try:
            url = f"https://pump.fun/{token_address}"
            self.driver.get(url)
            self.wait_for_page_load()

            try:
                # Wait for any loading indicator to disappear (if exists)
                WebDriverWait(self.driver, 5).until_not(
                    EC.presence_of_element_located((By.CLASS_NAME, "loading"))
                )
            except:
                pass

            try:
                # Try to find the description using JavaScript
                script = """
                return Array.from(document.getElementsByClassName('break-anywhere'))
                    .map(el => el.textContent.trim())
                    .filter(text => text.length > 0)[0];
                """
                description = self.driver.execute_script(script)
                
                if not description:
                    # Fallback to Selenium's element location
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "break-anywhere"))
                    )
                    description = element.text.strip()

                if description:
                    if self.debug:
                        print(f"Found description: {description[:50]}...")
                    
                    result = {
                        'token_address': token_address,
                        'description': description
                    }
                    self.description_cache[token_address] = result
                    return result
                else:
                    if self.debug:
                        print("No description found in elements")
                    return None

            except TimeoutException:
                if self.debug:
                    print("Timeout waiting for description element")
                return None
            
        except Exception as e:
            if self.debug:
                print(f"Error scraping token: {str(e)}")
            return None

    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass

def test_scraper():
    """Test function to verify scraper functionality"""
    test_tokens = [
        "A9e6JzPQstmz94pMnzxgyV14QUqoULSXuf5FPsq8UiRa",  # FIJI
        "6PbjXML6yTzjJD1ex7sGrXGbDAxTzRQsh9xEcVKQpump",  # thinspo
        "ARt4N4WY4PEdYUuBG7qENwuYSSiQUqP1RXFiahhwfzH9",  # EGIRL
        "HmAgiwjjP9CXqK5wQNsHKtjAt2CH3Kv8Q7xH5kGL2nqZ"   # Time Traveler
    ]
    
    scraper = PumpTokenScraper(use_headless=True, debug=True)
    try:
        for token in test_tokens:
            print(f"\nTesting token: {token}")
            info = scraper.get_token_description(token)
            if info:
                print(f"Success! Description: {info['description'][:100]}...")
            else:
                print("No description found")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_scraper()