import yfinance as yf
from etf_symbols import ETF_SYMBOLS

def fetch_all_etfs():
    data = yf.download(ETF_SYMBOLS, period="2d", progress=False, threads=True)
    out = []

    for s in ETF_SYMBOLS:
        try:
            df = data[s]
            prev = df["Close"].iloc[-2]
            curr = df["Close"].iloc[-1]
            chg = ((curr - prev) / prev) * 100
            out.append({
                "id": f"ETF:{s.replace('.NS','')}",
                "price": float(curr),
                "change": float(chg)
            })
        except Exception:
            pass

    return out
