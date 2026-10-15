# The Polite Scraper (FlyRank A9)

A polite, resilient web scraping pipeline built in Python that fetches, extracts, normalizes, and validates book data from a practice sandbox.

## Target Classification
* **Target Site:** Books to Scrape (`books.toscrape.com`)
* **Purpose:** This site is a public practice sandbox explicitly built for scraping experimentation.
* **Scope:** The scraper only collects data from the first 3 catalogue pages.
* **Data Collected:** Book title, product URL, price, availability, rating, description, source page, and fetch timestamp.
* **Appropriateness:** Scraping is appropriate here because the site is explicitly designed as a sandbox to practice these skills.
* **Robots.txt Result:** No robots file found.
* **Commitment:** I will not reuse this code on another site without checking its rules and terms first.

## Installation & Lane
**Lane:** Python 3.10+

1. Clone this repository and navigate to the `scraper` directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install requests beautifulsoup4 pydantic
   ```

## How to Run
Run the pipeline with a single command:
```bash
python src/main.py
```
The validated data will be saved to `output/books.json`, and the run report to `output/run-report.json`.

## Record Schema
Data is validated using Pydantic before storage to guarantee shape and types:
* `title` (string)
* `product_url` (absolute URL, used for deduplication/idempotency)
* `price_text` (string)
* `price_gbp` (float)
* `availability_text` (string)
* `rating_text` (string, optional)
* `description` (string, optional)
* `source_page` (absolute URL)
* `fetched_at` (ISO 8601 timestamp)

## Politeness Rules Followed
* **Identity:** Sends a clear `User-Agent` (`FlyRankInternship-A9/1.0`) with a repository link.
* **Rate Limiting:** Waits 0.5 seconds between requests to the live server.
* **Caching:** Saves HTML locally to `cache/`. Repeated runs do not hit the live server.
* **Timeouts:** Enforces a 10-second timeout on all requests.

## Architecture Notes
* **Why no browser?** The data for this site is fully contained within the raw HTML delivered by the initial HTTP response. Using a headless browser would add unnecessary overhead without providing any additional data.
* **Honest Limitation:** The pipeline relies heavily on the specific HTML structure. If the site redesigns its DOM, the CSS selectors will break and require updating.
* **Ethics Statement:** Always use an official API when one exists. Never bypass logins, paywalls, or blocks, and strictly collect only the data you need for the task.

## Sample Run Report
```json
{
  "start_time": "2026-10-15T11:00:00.000000+00:00",
  "duration_seconds": 113.42,
  "pages_fetched": 63,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```