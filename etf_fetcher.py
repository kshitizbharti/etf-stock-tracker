import yfinance as yf
from etf_symbols import ETF_SYMBOLS

def fetch_all_etfs():
    results = []

    for sym in ETF_SYMBOLS:
        try:
            t = yf.Ticker(sym)
            info = t.fast_info

            last = info.get("lastPrice")
            prev = info.get("previousClose")

            if not last or not prev:
                continue

            change = ((last - prev) / prev) * 100

            results.append({
                "id": f"ETF:{sym.replace('.NS','')}",
                "price": float(last),
                "change": float(change)
            })

        except Exception as e:
            print(f"ETF failed {sym}: {e}")

    return results
