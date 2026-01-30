import requests
import time

BASE_URL = "https://api.upstox.com/v2/market-quote/etfs"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://upstox.com/etfs"
}

def fetch_all_etfs():
    """
    Fetch all NSE ETFs from Upstox public API,
    sorted by worst 1D change (%).
    """

    results = []
    page = 1
    page_size = 50
    max_pages = 20  # safety cap

    while page <= max_pages:
        params = {
            "exchange": "NSE",
            "page": page,
            "pageSize": page_size,
            "sortBy": "oneDayChange",
            "sortOrder": "asc"  # worst performers first
        }

        try:
            r = requests.get(
                BASE_URL,
                headers=HEADERS,
                params=params,
                timeout=15
            )
        except Exception as e:
            print(f"Upstox ETF request failed: {e}")
            break

        if r.status_code != 200:
            print(f"Upstox ETF HTTP {r.status_code}")
            break

        data = r.json()

        items = data.get("data", [])
        if not items:
            break

        for etf in items:
            try:
                name = etf.get("name")
                price = etf.get("lastPrice")
                change = etf.get("oneDayChange")

                if price is None or change is None:
                    continue

                results.append({
                    "id": f"ETF:{name}",
                    "price": float(price),
                    "change": float(change)
                })

            except Exception:
                continue

        # stop if last page
        if len(items) < page_size:
            break

        page += 1
        time.sleep(0.3)  # be polite

    return results
