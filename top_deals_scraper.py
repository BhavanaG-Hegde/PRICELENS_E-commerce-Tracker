
import sqlite3
import requests
from bs4 import BeautifulSoup
import random
import time

def clean_product_name(name):
    """Extract the main part of the product name."""
    delimiters = ["|", "-", ","]
    for delimiter in delimiters:
        if delimiter in name:
            name = name.split(delimiter)[0]
            break
    return name.strip()

def top_deals(max_products=15):
    """Fetch top deals from Amazon."""
    url = f"https://www.amazon.in/s?k=best+deals+of+the+day"
    # url= f"https://www.amazon.in/s?k=top+deals+for+today"
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
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")

        for item in soup.select(".s-main-slot .s-result-item"):
            name_element = item.select_one("h2 span")
            price_element = item.select_one("span.a-price-whole")
            link_element = item.select_one("a.a-link-normal")
            image_element = item.select_one("img.s-image")
            bestseller_element = item.select_one(".a-badge-label")

            name = name_element.text.strip() if name_element else "Not found"
            name = clean_product_name(name)

            price = price_element.text.strip() if price_element else "Not found"
            link = link_element['href'] if link_element else "Not found"
            image_url = image_element['src'] if image_element else "Not found"
            bestseller_tag = bestseller_element.text.strip() if bestseller_element else "Not available"

            if link != "Not found" and not link.startswith("http"):
                link = f"https://www.amazon.in{link}"

            if name != "Not found" and price != "Not found" and link != "Not found" and image_url != "Not found":
                products.append({
                    "name": name,
                    "price": price,
                    "link": link,
                    "image_url": image_url,
                    "bestseller_tag": bestseller_tag
                })

                if len(products) >= max_products:
                    break

        next_page = soup.select_one("a.s-pagination-next")
        if not next_page or len(products) >= max_products:
            break

        url = f"https://www.amazon.in{next_page['href']}"
        time.sleep(2)

    return products

