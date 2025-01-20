# Import necessary libraries
from selenium import webdriver
import random
import time
import requests
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession
import nest_asyncio
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Apply patch to allow asyncio to work in Jupyter Notebooks
nest_asyncio.apply()

async def scrape_amazon_update(url, max_products=1):
    """Fetches the webpage and extracts product details using Selenium."""
    # # Configure the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no browser UI)
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options)
    products = []

    try:
        # Load the webpage
        driver.get(url)
        print("Page loaded successfully.")

        # Wait for the page to load the necessary elements
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )
        print("Page elements loaded.")

        # Extract product details
        

        price_element = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
        price = price_element.text.strip() if price_element else "Not found"


        # Add product details to the list

        print(f"Extracted price: {price}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the driver
        driver.quit()

    return price