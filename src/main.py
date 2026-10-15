import os
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime, timezone

CACHE_DIR = "cache"
HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/yourusername/scraper)"
}

def get_html(url, filename):
    """Fetches HTML and returns a tuple: (html_content, is_from_cache)"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        
    cache_path = os.path.join(CACHE_DIR, filename)
    
    # 1. Read from cache
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read(), True
            
    # 2. Fetch from live site
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            return response.text, False
        else:
            print(f"Failed to fetch {url}. Status: {response.status_code}")
            return None, False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None, False

def discover_books():
    current_url = "https://books.toscrape.com/catalogue/page-1.html"
    catalogue_pages = 0
    # Using a dictionary to map absolute URL -> source catalogue page
    discovered_links = {} 
    
    while current_url and catalogue_pages < 3:
        catalogue_pages += 1
        filename = f"catalogue-page-{catalogue_pages}.html"
        
        html, from_cache = get_html(current_url, filename)
        if not html:
            break
            
        if not from_cache:
            time.sleep(0.5) 
            
        soup = BeautifulSoup(html, "html.parser")
        
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and "href" in a_tag.attrs:
                abs_url = urljoin(current_url, a_tag["href"])
                if abs_url not in discovered_links:
                    discovered_links[abs_url] = current_url
        
        next_button = soup.select_one("li.next a")
        if next_button and catalogue_pages < 3:
            current_url = urljoin(current_url, next_button["href"])
        else:
            current_url = None
            
    return discovered_links

def extract_book_details(book_url, source_page):
    """Fetches a single book page and extracts the raw record"""
    # Create a safe, unique filename for the cache based on the URL ending
    cache_filename = f"book-{book_url.rstrip('/').split('/')[-1]}"
    if not cache_filename.endswith(".html"):
        cache_filename += ".html"
        
    html, from_cache = get_html(book_url, cache_filename)
    if not html:
        return None
        
    if not from_cache:
        time.sleep(0.5)
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Aim selectors directly at the product area
    product_main = soup.select_one("div.product_main")
    if not product_main:
        return None
        
    title_elem = product_main.select_one("h1")
    price_elem = product_main.select_one("p.price_color")
    availability_elem = product_main.select_one("p.instock.availability")
    
    # The rating is stored as the second class name in the star-rating paragraph
    rating_elem = product_main.select_one("p.star-rating")
    rating_text = rating_elem["class"][1] if rating_elem and len(rating_elem["class"]) > 1 else None
    
    # The description is the next sibling paragraph after the #product_description div
    desc_heading = soup.select_one("#product_description")
    desc_elem = desc_heading.find_next_sibling("p") if desc_heading else None
    
    # Build the 8-field raw record keeping source_page and fetched_at as provenance
    return {
        "title": title_elem.text if title_elem else None,
        "product_url": book_url,
        "price_text": price_elem.text if price_elem else None,
        "availability_text": availability_elem.text.strip() if availability_elem else None,
        "rating_text": rating_text,
        "description": desc_elem.text if desc_elem else None,  # Will correctly be None if missing[cite: 4]
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    book_links = discover_books()
    
    raw_records = []
    print("Extracting book details... (this will take ~30 seconds on the first run)")
    
    for url, source in book_links.items():
        record = extract_book_details(url, source)
        if record:
            raw_records.append(record)
            
    # Stage 3 Checkpoint: Print one complete record and the total count[cite: 4]
    if raw_records:
        import json
        print("\n--- SAMPLE RECORD ---")
        print(json.dumps(raw_records[0], indent=2))
        print("---------------------\n")
        
    print(f"detail_pages = {len(raw_records)}")