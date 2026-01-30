import requests
from bs4 import BeautifulSoup
import yfinance as yf

# ===============================
# Upstox config
# ===============================
UPSTOX_URL = "https://upstox.com/etfs/?page={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ===============================
# Yahoo Finance fallback ETF list
# (Stable + works on GitHub Actions)
# ===============================
YF_ETFS = [
    "SILVERBEES.NS",
    "GOLDBEES.NS",
    "NIFTYBEES.NS",
    "BANKBEES.NS",
    "JUNIORBEES.NS",
    "ITBEES.NS",
    "PHARMABEES.NS",
    "AUTOBEES.NS",
    "ENERGYBEES.NS",
    "CPSEETF.NS",
    "PSUBNKBEES.NS",
    "MID150BEES.NS",
    "MON100.NS",
    "SETFNIF50.NS",
    "SETFNIFBK.NS",
]

# ===============================
# Helpers
# ===============================
def _parse_float(text: str) -> float:
    cleaned = (
        text.replace("₹", "")
            .replace("%", "")
            .replace(",", "")
            .replace("−", "-")
            .replace("–", "-")
            .strip()
    )
    return float(cleaned)

# ===============================
# Upstox scraper (best effort)
# ===============================
def _fetch_from_upstox():
    results = []
    seen_first = None
    page = 1

    while page <= 20:
        try:
            r = requests.get(UPSTOX_URL.format(page), headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break
        except Exception:
            break

        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select("tbody tr")
        if not rows:
            break

        first_name = rows[0].find_all("td")[0].get_text(strip=True)
        if first_name == seen_first:
            break
        seen_first = first_name

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

# ===============================
# Yahoo Finance fallback
# ===============================
def _fetch_from_yfinance():
    data = yf.download(
        tickers=YF_ETFS,
        period="2d",
        group_by="ticker",
        threads=True,
        progress=False
    )

    results = []

    for sym in YF_ETFS:
        try:
            df = data[sym]
            if len(df) < 2:
                continue

            prev = df["Close"].iloc[-2]
            curr = df["Close"].iloc[-1]
            change = ((curr - prev) / prev) * 100

            results.append({
                "id": f"ETF:{sym.replace('.NS','')}",
                "name": sym.replace(".NS", ""),
                "price": float(curr),
                "change": float(change)
            })
        except Exception:
            continue

    return results

# ===============================
# Public API (used by tracker.py)
# ===============================
def fetch_all_etfs():
    """
    1. Try Upstox (best data)
    2. If blocked / empty → fallback to Yahoo Finance
    """
    etfs = _fetch_from_upstox()

    if etfs:
        return etfs

    # Guaranteed fallback
    return _fetch_from_yfinance()
