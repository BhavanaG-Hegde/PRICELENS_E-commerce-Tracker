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

# setup ="C:\chrome-win\chrome-win\chrome.exe"

# Scrape product details using requests and BeautifulSoup (for static pages)
def scrape_amazon_static(query, max_products=20):
    base_url = "https://www.amazon.in/s?k="
    url = f"{base_url}{query.replace(' ', '+')}"

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]

    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.amazon.in/"
    }

    products = []
    current_page = 1

    while len(products) < max_products:
        # Send GET request to Amazon
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            break

        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Scrape product details
        for item in soup.select(".s-main-slot .s-result-item"):
            name_element = item.select_one("h2 span")
            price_element = item.select_one("span.a-price-whole")
            link_element = item.select_one("a.a-link-normal")
            image_element = item.select_one("img.s-image")

            name = name_element.text.strip() if name_element else "Not found"
            price = price_element.text.strip() if price_element else "Not found"
            link = link_element['href'] if link_element else "Not found"
            image_url = image_element['src'] if image_element else "Not found"

            if link != "Not found" and not link.startswith("http"):
                link = f"https://www.amazon.in{link}"

            if name != "Not found" and price != "Not found" and link != "Not found" and image_url != "Not found":
                products.append({
                    "name": name,
                    "price": price,
                    "link": link,
                    "image_url": image_url
                })
                print(f"Name: {name}\nPrice: ₹{price}\nLink: {link}\nImage URL: {image_url}\n{'-' * 50}")

                if len(products) >= max_products:
                    break

        # Find the "Next" page link
        next_page = soup.select_one("a.s-pagination-next")
        if not next_page or len(products) >= max_products:
            break

        url = f"https://www.amazon.in{next_page['href']}"
        current_page += 1

        # Sleep to avoid being blocked
        time.sleep(2)

    return products

async def scrape_amazon_dynamic(url, max_products=1):
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
        name_element = driver.find_element(By.ID, "productTitle")
        name = name_element.text.strip() if name_element else "Not found"

        price_element = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
        price = price_element.text.strip() if price_element else "Not found"

        image_element = driver.find_element(By.CSS_SELECTOR, "img.a-dynamic-image")
        image_url = image_element.get_attribute("src") if image_element else "Not found"

        # Add product details to the list
        if name != "Not found" and price != "Not found" and image_url != "Not found":
            products.append({
                "name": name,
                "price": price,
                "link": url,
                "image_url": image_url,
            })

        print(f"Extracted product: {products}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the driver
        driver.quit()

    return products

# Combined function to handle both static and dynamic pages
async def scrape_amazon(query_or_url):
    """Fetch product details from Amazon based on query (search term) or URL."""

    if query_or_url.startswith("http"):
        # If it's a URL, scrape the dynamic page
        print("Scraping product details from URL...")
        return await scrape_amazon_dynamic(query_or_url)
    else:
        # Otherwise, treat it as a search query and scrape static pages
        print("Scraping product details from query...")
        return scrape_amazon_static(query_or_url)



