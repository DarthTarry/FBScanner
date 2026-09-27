import asyncio
import argparse
import json
import os
import sqlite3
import time
from urllib.parse import quote

# Configuration
ZIP_CODES = ["08502", "07310"]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6141714840")
COOKIE_FILE = os.getenv("FB_COOKIE_FILE", "fb_cookies.json")

# Comprehensive search queries matching your target component list
QUERIES = [
    "Ryzen 5600", "Ryzen 5800X3D", "Ryzen 5700X", "Ryzen 5900X", "Ryzen 5 5500",
    "AM4 Motherboard", "AM5 Motherboard", "B550 Motherboard", "X570 Motherboard",
    "850w PSU", "1000w PSU", "Corsair PSU 850",
    "DDR4 RAM", "DDR5 RAM",
    "NVMe SSD", "NVMe SSD",
    "PC Case"
]
DISTANCE_OPTIONS = {
    "5 miles": 5,
    "10 miles": 10,
    "25 miles": 25,
    "50 miles": 50,
    "100 miles": 100,
}

def init_db():
    conn = sqlite3.connect("market_agent.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_listings (
            id TEXT PRIMARY KEY,
            title TEXT,
            price TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()

def normalize_cookies(cookies):
    normalized = []
    for cookie in cookies:
        item = {
            key: cookie[key]
            for key in ("name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite")
            if key in cookie
        }
        if "expirationDate" in cookie and "expires" not in item:
            item["expires"] = cookie["expirationDate"]

        same_site = item.get("sameSite")
        same_site_map = {
            "no_restriction": "None",
            "unspecified": None,
            "lax": "Lax",
            "strict": "Strict",
            "none": "None",
        }
        if isinstance(same_site, str):
            item["sameSite"] = same_site_map.get(same_site.lower(), same_site)
        if item.get("sameSite") is None:
            item.pop("sameSite", None)
        normalized.append(item)
    return normalized

def select_search_criteria():
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("MPScan Search Criteria")
    root.resizable(False, False)

    selected_zips = {zip_code: tk.BooleanVar(value=True) for zip_code in ZIP_CODES}
    selected_queries = {query: tk.BooleanVar(value=True) for query in QUERIES}
    distance = tk.StringVar(value="25 miles")
    result = {"zips": [], "queries": [], "distance": 25, "cancelled": True}

    container = ttk.Frame(root, padding=12)
    container.grid()

    ttk.Label(container, text="Select ZIP codes").grid(row=0, column=0, sticky="w")
    zip_frame = ttk.Frame(container)
    zip_frame.grid(row=1, column=0, sticky="w", padx=(8, 0), pady=(2, 10))
    for index, (zip_code, variable) in enumerate(selected_zips.items()):
        ttk.Checkbutton(zip_frame, text=zip_code, variable=variable).grid(
            row=index // 3, column=index % 3, sticky="w", padx=(0, 16)
        )

    ttk.Label(container, text="Select search queries").grid(row=2, column=0, sticky="w")
    query_frame = ttk.Frame(container)
    query_frame.grid(row=3, column=0, sticky="w", padx=(8, 0), pady=(2, 10))
    for index, (query, variable) in enumerate(selected_queries.items()):
        ttk.Checkbutton(query_frame, text=query, variable=variable).grid(
            row=index // 2, column=index % 2, sticky="w", padx=(0, 24)
        )

    ttk.Label(container, text="Search distance").grid(row=4, column=0, sticky="w")
    ttk.Combobox(
        container,
        textvariable=distance,
        values=list(DISTANCE_OPTIONS),
        state="readonly",
        width=15,
    ).grid(row=5, column=0, sticky="w", padx=(8, 0), pady=(2, 10))

    def select_all(value):
        for variable in [*selected_zips.values(), *selected_queries.values()]:
            variable.set(value)

    button_frame = ttk.Frame(container)
    button_frame.grid(row=6, column=0, sticky="e")
    ttk.Button(button_frame, text="Select All", command=lambda: select_all(True)).grid(
        row=0, column=0, padx=(0, 6)
    )
    ttk.Button(button_frame, text="Clear All", command=lambda: select_all(False)).grid(
        row=0, column=1, padx=(0, 6)
    )

    def start_scan():
        chosen_zips = [zip_code for zip_code, variable in selected_zips.items() if variable.get()]
        chosen_queries = [query for query, variable in selected_queries.items() if variable.get()]
        if not chosen_zips or not chosen_queries:
            missing = []
            if not chosen_zips:
                missing.append("at least one ZIP code")
            if not chosen_queries:
                missing.append("at least one search query")
            messagebox.showwarning(
                "Incomplete search criteria",
                "Please select " + " and ".join(missing) + ".",
                parent=root,
            )
            return

        result["zips"] = chosen_zips
        result["queries"] = chosen_queries
        result["distance"] = DISTANCE_OPTIONS[distance.get()]
        result["cancelled"] = False
        root.destroy()

    ttk.Button(button_frame, text="Start Scan", command=start_scan).grid(row=0, column=2)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

    if result["cancelled"] or not result["zips"] or not result["queries"]:
        return [], [], 0
    return result["zips"], result["queries"], result["distance"]

def resend_existing_alerts(limit=None):
    conn = sqlite3.connect("market_agent.db")
    query = "SELECT title, price, url FROM seen_listings ORDER BY rowid"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    listings = conn.execute(query, params).fetchall()
    conn.close()

    print(f"Resending {len(listings)} stored listing(s)...")
    delivered = 0
    for title, price, url in listings:
        message = (
            "🔥 *Stored Deal*\n"
            f"*Item:* {title}\n"
            f"*Price:* {price}"
        )
        if send_telegram_alert(message, url):
            delivered += 1
        time.sleep(0.1)

    print(f"Delivered {delivered}/{len(listings)} stored alert(s).")

def send_telegram_alert(message, url):
    if (
        not TELEGRAM_BOT_TOKEN
        or TELEGRAM_BOT_TOKEN.startswith("PASTE_")
        or not TELEGRAM_CHAT_ID
    ):
        print(f"\n[Console Alert]:\n{message}\nLink: {url}\n" + "-"*40)
        return False

    import requests
        
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"{message}\n\nLink: {url}",
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            print(f"Telegram rejected the alert: {result}")
            return False
        return True
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False

async def dismiss_facebook_login_prompt(page):
    if "/login" in page.url:
        print("Facebook redirected to login; valid cookies are required to scan Marketplace.")
        return False

    close_button = page.locator('div[role="dialog"] button[aria-label="Close"]').first
    if await close_button.count():
        try:
            await close_button.click(timeout=3000)
            print("Closed the Facebook login prompt.")
        except Exception:
            pass
    return True

async def scrape_facebook_marketplace(page, query, zip_code, distance):
    encoded_query = quote(query)
    search_url = (
        f"https://www.facebook.com/marketplace/{zip_code}/search/"
        f"?query={encoded_query}&radius={distance}"
    )
    print(f"Navigating to: {search_url}")
    try:
        await page.goto(search_url, timeout=60000)
        await page.wait_for_timeout(6000) # Allow dynamic content/JS to render
        if not await dismiss_facebook_login_prompt(page):
            return []
    except Exception as e:
        print(f"Error navigating to page: {e}")
        return []
    
    listings = []
    try:
        # Resilient selector targeting marketplace item links
        item_links = await page.locator('a[href*="/marketplace/item/"]').all()
        
        seen_urls = set()
        for link in item_links[:12]: # Check top 12 results per query
            try:
                relative_url = await link.get_attribute('href')
                if not relative_url:
                    continue
                
                full_url = relative_url if relative_url.startswith("http") else f"https://www.facebook.com{relative_url}"
                base_url = full_url.split('?')[0] # Remove tracking query parameters
                
                if base_url in seen_urls:
                    continue
                seen_urls.add(base_url)
                
                # Extract unique item ID from URL
                if '/item/' in base_url:
                    listing_id = base_url.split('/item/')[1].split('/')[0]
                else:
                    listing_id = base_url

                # Extract text inside the card to isolate title and price
                card_text = await link.inner_text()
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                
                title = "Unknown Item"
                price = "Price not listed"
                
                for line in lines:
                    if line.startswith('$'):
                        price = line
                    elif len(line) > 3 and title == "Unknown Item":
                        title = line

                listings.append({
                    "id": listing_id,
                    "title": title,
                    "price": price,
                    "url": base_url
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Error parsing listings for query '{query}': {e}")

    return listings

async def run_agent(zip_codes, queries, distance):
    from playwright.async_api import async_playwright

    init_db()
    conn = sqlite3.connect("market_agent.db")
    cursor = conn.cursor()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # Load exported cookies if available
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, "r") as f:
                    cookies = json.load(f)
                cookies = normalize_cookies(cookies)
                await context.add_cookies(cookies)
                print(f"Successfully loaded {len(cookies)} cookies from {COOKIE_FILE}.")
            except Exception as e:
                print(f"Error loading cookies: {e}")
        else:
            print(f"ℹ️ Notice: '{COOKIE_FILE}' not found. If Facebook blocks the feed, export your cookies into this directory.")

        page = await context.new_page()

        for zip_code in zip_codes:
            for query in queries:
                print(f"\nScraping '{query}' near {zip_code}...")
                listings = await scrape_facebook_marketplace(page, query, zip_code, distance)
                print(f"Found {len(listings)} items for '{query}'.")
                
                for listing in listings:
                    cursor.execute("SELECT id FROM seen_listings WHERE id = ?", (listing["id"],))
                    if not cursor.fetchone():
                        # New listing found!
                        msg = f"🔥 *New Deal Found!*\n*Item:* {listing['title']}\n*Price:* {listing['price']}\n*Search:* {query} ({zip_code})"
                        if send_telegram_alert(msg, listing["url"]):
                            # Save only after Telegram confirms delivery.
                            cursor.execute("INSERT INTO seen_listings VALUES (?, ?, ?, ?)",
                                           (listing["id"], listing["title"], listing["price"], listing["url"]))
                            conn.commit()
                        
                await asyncio.sleep(6) # Polite delay between requests to avoid rate limits

        await browser.close()
    conn.close()

def parse_search_criteria(args):
    if args.interactive:
        return select_search_criteria()

    zip_codes = args.zip_codes or ZIP_CODES
    queries = args.queries or QUERIES
    return zip_codes, queries, args.distance

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--zip",
        dest="zip_codes",
        action="append",
        help="ZIP code to scan; repeat for multiple ZIP codes.",
    )
    parser.add_argument(
        "--query",
        dest="queries",
        action="append",
        help="Marketplace query to scan; repeat for multiple queries.",
    )
    parser.add_argument(
        "--distance",
        type=int,
        choices=sorted(DISTANCE_OPTIONS.values()),
        default=25,
        help="Search radius in miles (default: 25).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use the desktop popup instead of server-friendly command-line options.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Repeat the scan every N seconds; 0 runs one scan and exits.",
    )
    parser.add_argument(
        "--resend-existing",
        action="store_true",
        help="Send stored listings from market_agent.db to Telegram.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of stored listings to resend.",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.interval < 0:
        parser.error("--interval cannot be negative")

    if args.resend_existing:
        resend_existing_alerts(args.limit)
    else:
        selected_zips, selected_queries, distance = parse_search_criteria(args)
        if not selected_zips or not selected_queries:
            parser.error("at least one ZIP code and one query are required")
        else:
            while True:
                asyncio.run(run_agent(selected_zips, selected_queries, distance))
                if args.interval == 0:
                    break
                print(f"Scan complete; next scan in {args.interval} seconds.")
                time.sleep(args.interval)