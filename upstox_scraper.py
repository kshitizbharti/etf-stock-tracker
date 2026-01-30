import requests
from bs4 import BeautifulSoup

BASE_URL = "https://upstox.com/etfs/?page={}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def _parse_float(text: str) -> float:
    """
    Safely parse numeric strings coming from Upstox.
    Handles:
    - Unicode minus (−)
    - En dash (–)
    - Percent sign
    - Commas
    """
    if not text:
        raise ValueError("Empty numeric text")

    cleaned = (
        text.replace("₹", "")
            .replace("%", "")
            .replace(",", "")
            .replace("−", "-")
            .replace("–", "-")
            .strip()
    )
    return float(cleaned)

def fetch_all_etfs():
    page = 1
    results = []
    seen_first_name = None

    while page <= 20:  # HARD STOP to avoid infinite pagination
        try:
            r = requests.get(BASE_URL.format(page), headers=HEADERS, timeout=20)
            r.raise_for_status()
        except Exception:
            break

        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select("tbody tr")

        if not rows:
            break

        # Detect repeated pages (Upstox loops last page)
        first_name = rows[0].find_all("td")[0].get_text(strip=True)
        if seen_first_name == first_name:
            break
        seen_first_name = first_name

        for row in rows:
            try:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                name = cols[0].get_text(strip=True)
                price = _parse_float(cols[3].get_text(strip=True))
                change = _parse_float(cols[4].get_text(strip=True))

                results.append({
                    "id": f"ETF:{name}",
                    "name": name,
                    "price": price,
                    "change": change
                })
            except Exception:
                continue

        page += 1

    return results
