import requests
from bs4 import BeautifulSoup

BASE_URL = "https://upstox.com/etfs/?page={}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_all_etfs():
    page = 1
    results = []
    seen_first_name = None

    while True:
        r = requests.get(BASE_URL.format(page), headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select("tbody tr")

        if not rows:
            break

        # Detect infinite pagination
        first_name = rows[0].find_all("td")[0].get_text(strip=True)
        if seen_first_name == first_name:
            break
        seen_first_name = first_name

        for row in rows:
            cols = row.find_all("td")
            name = cols[0].get_text(strip=True)
            price = float(cols[3].get_text(strip=True).replace("₹","").replace(",",""))
            change = float(cols[4].get_text(strip=True).replace("%",""))

            results.append({
                "id": f"ETF:{name}",
                "name": name,
                "price": price,
                "change": change
            })

        page += 1

    return results


