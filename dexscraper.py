print("Importing Libraries")
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from seleniumbase import Driver

# Scrape Dex Screener For Data
def scrapeDex(token):
    # Initialize the URLs - Add the first pages of the genre to scrap
    url = f"https://dexscreener.com/solana/{token}"             # First Page of New Pairs  
    
    # Initialize Driver
    # driver = uc.Chrome()
    driver = Driver(uc=True, headless=True)  # Set headless=True here
    driver.get(url)  # Open the first URL

    # Will be used for Dall-E ~ Get the image URL
    # image_element = WebDriverWait(driver, 10).until(
    #    EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div/div/div[1]/div/div[1]/div[6]/div/div/div[1]/button/img"))
    #)
    #image_url = image_element.get_attribute('src')  # Get the 'src' attribute of the img tag

    #print(f"Image URL: {image_url}")  # Print the image URL

    element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div/div/div[1]/div/div[1]/div[6]/div/div/p"))
    )

    # Return the text of the element
    return(element.text)


# Run the following when program is executed
if __name__ == "__main__":
    scrapeDex("A9e6JzPQstmz94pMnzxgyV14QUqoULSXuf5FPsq8UiRa")