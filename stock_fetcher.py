import yfinance as yf

STOCKS = [
    "HUDCO.NS","IRCTC.NS","SBIN.NS","TATASTEEL.NS","RELIANCE.NS"
]

def fetch_stocks():
    data = yf.download(STOCKS, period="2d", progress=False, threads=True)
    out = []

    for s in STOCKS:
        try:
            df = data[s]
            prev = df["Close"].iloc[-2]
            curr = df["Close"].iloc[-1]
            chg = ((curr - prev) / prev) * 100
            out.append({
                "id": f"STOCK:{s.replace('.NS','')}",
                "price": float(curr),
                "change": float(chg)
            })
        except Exception:
            pass

    return out
