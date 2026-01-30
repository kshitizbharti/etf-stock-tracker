import os
from state import load_state, save_state
from market import is_market_hours, now_ist
from etf_fetcher import fetch_all_etfs
from stock_fetcher import fetch_stocks
from notifier import send

# =========================
# Threshold slabs
# =========================
ETF_THRESHOLDS = [-2.5, -3.5, -5.0, -8.0, -10.0]
STOCK_THRESHOLDS = [-5.0, -8.0, -10.0]

# =========================
# Secrets
# =========================
BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

# =========================
# Detect manual run
# =========================
IS_MANUAL_RUN = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

# =========================
# Load state
# =========================
state = load_state()
now = now_ist()
market_open = is_market_hours()

# =========================
# Fetch data
# =========================
etfs = []
stocks = []

if market_open:
    etfs = fetch_all_etfs()
    stocks = fetch_stocks()

# =========================
# 🔴 ALWAYS SEND DEBUG MESSAGE ON MANUAL RUN
# =========================
if IS_MANUAL_RUN:
    worst_etf = min([e["change"] for e in etfs], default=None)
    worst_stock = min([s["change"] for s in stocks], default=None)

    send(
        BOT,
        CHAT,
        "🧪 <b>MANUAL RUN DEBUG</b>\n"
        f"Time (IST): {now.strftime('%H:%M:%S')}\n"
        f"Market hours: {market_open}\n"
        f"ETFs fetched: {len(etfs)}\n"
        f"Stocks fetched: {len(stocks)}\n"
        f"Worst ETF %: {worst_etf}\n"
        f"Worst Stock %: {worst_stock}"
    )

# =========================
# Alert logic
# =========================
if market_open:
    for item in etfs + stocks:

        thresholds = (
            ETF_THRESHOLDS
            if item["id"].startswith("ETF:")
            else STOCK_THRESHOLDS
        )

        crossed = None
        for t in sorted(thresholds, reverse=True):
            if item["change"] <= t:
                crossed = t

        if crossed is None:
            continue

        prev = state["alerted"].get(item["id"])

        should_alert = (
            prev is None or
            prev > crossed or
            IS_MANUAL_RUN
        )

        if should_alert:
            send(
                BOT,
                CHAT,
                f"🚨 <b>{item['id']}</b>\n"
                f"Change: {item['change']:.2f}%\n"
                f"Price: ₹{item['price']:.2f}\n"
                f"Slab: {crossed}%"
            )
            state["alerted"][item["id"]] = crossed

# =========================
# Save state
# =========================
save_state(state)
