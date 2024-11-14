import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
from selenium.common.exceptions import TimeoutException, WebDriverException
from multiprocessing import Process, Queue
import logging

logging.basicConfig(level=logging.INFO)
def scrapeDex(token, output_queue, max_retries=4, initial_retry_delay=0.5, max_retry_delay=2):
    url = f"https://dexscreener.com/solana/{token}"
    
    main_xpath = "/html/body/div[1]/div/main/div/div/div[1]/div/div[1]/div[6]/div/div/p"
    fallback_xpaths = [
        "/html/body/div[1]/div/main/div/div/div[1]/div/div[1]/div[5]/div/div/p",
        "/html/body/div[1]/div/main/div/div/div[1]/div/div[1]/div[6]/div/div/p"
        "/html/body/div[1]/div/main/div/div/div[1]/div/div[1]/div[6]/div/div/div[2]/div[1]/div/div/div/p"
    ]
    
    attempt = 0
    retry_delay = initial_retry_delay
    
    while attempt < max_retries:
        logging.info(f"Attempt {attempt + 1} for {token}")
        attempt += 1
        driver = None
        
        # Log time for browser initialization
        browser_start_time = time.time()
        for init_attempt in range(3):
            try:
                driver = Driver(uc=True, headless=True)
                logging.info(f"Browser initialized for {token} in {time.time() - browser_start_time:.2f} seconds.")
                break
            except WebDriverException as init_error:
                time.sleep(1)
        else:
            logging.error(f"Failed to initialize browser for {token}.")
            output_queue.put((token, None))
            return

        try:
            # Measure and log driver.get time
            page_load_start = time.time()
            driver.get(url)
            logging.info(f"driver.get({url}) completed for {token} in {time.time() - page_load_start:.2f} seconds.")

            # Step 1: Try main element
            main_element_start = time.time()
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, main_xpath))
                )
                logging.info(f"Main element found for {token} in {time.time() - main_element_start:.2f} seconds.")
                output_queue.put((token, element.text))
                return
            except TimeoutException:
                logging.warning(f"Main element not found for {token}. Attempting fallback...")

            # Step 2: Try fallback elements
            for xpath in fallback_xpaths:
                fallback_start = time.time()
                try:
                    fallback_element = WebDriverWait(driver, 1).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    logging.info(f"Fallback element found for {token} using {xpath} in {time.time() - fallback_start:.2f} seconds.")
                    output_queue.put((token, fallback_element.text))
                    return
                except TimeoutException:
                    pass
                    #logging.info(f"Fallback {xpath} not found for {token}, checked in {time.time() - fallback_start:.2f} seconds.")
                    
            logging.info(f"No description found for {token} after main and fallback checks.")
        
        except Exception as e:
            logging.error(f"Error during scraping {token}: {e}")
            output_queue.put((token, f"Error: {e}"))
        
        finally:
            if driver:
                driver.quit()
                #logging.info(f"Browser closed for {token}.")
        
        # Retry entire process after delay
        if attempt < max_retries:
            logging.info(f"Retrying token {token} after {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay + 0.5, max_retry_delay)
        else:
            output_queue.put((token, None))  # Final failure after all retries

def run_scrapers(tokens):
    processes = []
    output_queue = Queue()
    
    # Start all processes
    for token in tokens:
        process = Process(target=scrapeDex, args=(token, output_queue))
        processes.append(process)
        process.start()
        #time.sleep(0.1)  # Slight stagger to avoid overwhelming resources

    results = []

    # Collect results as they come in
    while any(p.is_alive() for p in processes) or not output_queue.empty():
        while not output_queue.empty():
            results.append(output_queue.get())
    
        #time.sleep(0.1)  # Small delay to reduce busy-waiting

    # Ensure all processes are joined
    for process in processes:
        process.join()

    return results

def main():
    # Define 4 test tokens representing different cases
    test_tokens = [
        "6PbjXML6yTzjJD1ex7sGrXGbDAxTzRQsh9xEcVKQpump",  # Case 1: Token with main description
        "Do3aZ2zeTYFVZg2d473PvkEvw6QtmYc3gUUugoQQEMbo",  # Case 2: Token with 'community takeover' and additional description
    ]

    # Run scrapers on test tokens
    results = run_scrapers(test_tokens)

    # Print results
    for token, description in results:
        logging.info(f"Token: {token}, Description: {description}")

if __name__ == "__main__":
    main()
    