import yfinance as yf
from etf_symbols import ETF_SYMBOLS

def fetch_all_etfs():
    results = []

    for sym in ETF_SYMBOLS:
        try:
            df = yf.download(
                sym,
                period="2d",
                interval="1m",
                progress=False
            )

            if df is None or len(df) < 2:
                continue

            prev = df["Close"].iloc[-2]
            curr = df["Close"].iloc[-1]

            if prev == 0:
                continue

            change = ((curr - prev) / prev) * 100

            results.append({
                "id": f"ETF:{sym.replace('.NS','')}",
                "price": float(curr),
                "change": float(change)
            })

        except Exception as e:
            print(f"ETF fetch failed for {sym}: {e}")

    return results
