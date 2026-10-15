import os
import requests

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "catalogue-page-1.html")
TARGET_URL = "https://books.toscrape.com/catalogue/page-1.html"

# A polite scraper always identifies itself
HEADERS = {
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/yourusername/scraper)"
}

def fetch_page():
    # Ensure the cache directory exists
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    # 1. Read from cache if it exists
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {len(html)} bytes")
        return html

    # 2. Otherwise, fetch from the live site
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=10)
        
        # Check status code before doing anything else
        if response.status_code == 200:
            html = response.text
            # Save the HTML to cache
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"FETCH: {len(html)} bytes")
            return html
        else:
            print(f"Failed to fetch. Status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    fetch_page()