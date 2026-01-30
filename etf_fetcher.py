import yfinance as yf
from etf_symbols import ETF_SYMBOLS

def fetch_all_etfs():
    data = yf.download(
        tickers=ETF_SYMBOLS,
        period="2d",
        group_by="ticker",
        threads=True,
        progress=False
    )

    results = []

    for sym in ETF_SYMBOLS:
        try:
            df = data[sym]
            if len(df) < 2:
                continue

            prev = df["Close"].iloc[-2]
            curr = df["Close"].iloc[-1]
            change = ((curr - prev) / prev) * 100

            results.append({
                "id": f"ETF:{sym.replace('.NS','')}",
                "name": sym.replace(".NS",""),
                "price": float(curr),
                "change": float(change)
            })
        except Exception:
            continue

    return results
