import os
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

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
    discovered_links = []
    
    # Stop after 3 pages or if there is no next page
    while current_url and catalogue_pages < 3:
        catalogue_pages += 1
        filename = f"catalogue-page-{catalogue_pages}.html"
        
        html, from_cache = get_html(current_url, filename)
        if not html:
            break
            
        # Wait 0.5s between real requests[cite: 4]
        if not from_cache:
            time.sleep(0.5) 
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Collect the link to every book on the page[cite: 4]
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and "href" in a_tag.attrs:
                # Turn relative URLs into absolute URLs[cite: 4]
                abs_url = urljoin(current_url, a_tag["href"])
                discovered_links.append(abs_url)
        
        # Follow the catalogue's own "next" link[cite: 4]
        next_button = soup.select_one("li.next a")
        if next_button and catalogue_pages < 3:
            current_url = urljoin(current_url, next_button["href"])
        else:
            current_url = None
            
    # Remove duplicate links[cite: 4]
    unique_urls = list(set(discovered_links))
    
    print(f"catalogue_pages = {catalogue_pages}")
    print(f"discovered = {len(discovered_links)}")
    print(f"unique_urls = {len(unique_urls)}")
    
    return unique_urls

if __name__ == "__main__":
    discover_books()