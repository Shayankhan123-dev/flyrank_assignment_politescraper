import os
import time
import requests
import json
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl, ValidationError
from typing import Optional

CACHE_DIR = "cache"
OUTPUT_DIR = "output"
HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/yourusername/scraper)"
}

# --- STAGE 4: Define the Schema ---
class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str]
    description: Optional[str]
    source_page: HttpUrl
    fetched_at: str

def get_html(url, filename):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        
    cache_path = os.path.join(CACHE_DIR, filename)
    
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read(), True
            
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
    cache_filename = f"book-{book_url.rstrip('/').split('/')[-1]}"
    if not cache_filename.endswith(".html"):
        cache_filename += ".html"
        
    html, from_cache = get_html(book_url, cache_filename)
    if not html:
        return None
        
    if not from_cache:
        time.sleep(0.5)
        
    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one("div.product_main")
    if not product_main:
        return None
        
    title_elem = product_main.select_one("h1")
    price_elem = product_main.select_one("p.price_color")
    availability_elem = product_main.select_one("p.instock.availability")
    
    rating_elem = product_main.select_one("p.star-rating")
    rating_text = rating_elem["class"][1] if rating_elem and len(rating_elem["class"]) > 1 else None
    
    desc_heading = soup.select_one("#product_description")
    desc_elem = desc_heading.find_next_sibling("p") if desc_heading else None
    
    return {
        "title": title_elem.text if title_elem else None,
        "product_url": book_url,
        "price_text": price_elem.text if price_elem else None,
        "availability_text": availability_elem.text.strip() if availability_elem else None,
        "rating_text": rating_text,
        "description": desc_elem.text if desc_elem else None,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

def clean_price(price_text: str) -> float:
    """Extracts numeric digits and decimal from messy price strings"""
    if not price_text:
        return 0.0
    match = re.search(r"[\d\.]+", price_text)
    return float(match.group()) if match else 0.0

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    book_links = discover_books()
    raw_records = []
    print("Extracting and normalizing records...")
    
    for url, source in book_links.items():
        record = extract_book_details(url, source)
        if record:
            # 1. Add the clean numeric price
            record["price_gbp"] = clean_price(record.get("price_text", ""))
            raw_records.append(record)
            
    # --- STAGE 4: Validate and Store ---
    validated_records = {} # Dictionary ensures idempotency using URL as key
    errors = []
    
    for raw in raw_records:
        try:
            # Validate against Pydantic schema[cite: 5]
            book = BookRecord(**raw)
            # Use absolute URL as canonical identity[cite: 5]
            url_key = str(book.product_url)
            # model_dump(mode='json') safely serializes HttpUrl objects
            validated_records[url_key] = book.model_dump(mode='json') 
        except ValidationError as e:
            # Route failures to errors with reason[cite: 5]
            errors.append({
                "record": raw,
                "error": e.errors()
            })

    # Write to files[cite: 5]
    with open(os.path.join(OUTPUT_DIR, "books.json"), "w", encoding="utf-8") as f:
        json.dump(list(validated_records.values()), f, indent=2)
        
    with open(os.path.join(OUTPUT_DIR, "errors.json"), "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2)

    print(f"Saved {len(validated_records)} valid records to output/books.json")
    if errors:
        print(f"Saved {len(errors)} invalid records to output/errors.json")