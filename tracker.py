from state import load_state, save_statea
from market import is_market_hours, now_ist
from upstox_scraper import fetch_all_etfs
from stock_fetcher import fetch_stocks
from notifier import send
import os

# ===== Threshold slabs =====
ETF_THRESHOLDS = [-2.5, -3.5, -5.0, -8.0, -10.0]
STOCK_THRESHOLDS = [-5.0, -8.0, -10.0]

# ===== Secrets =====
BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

# ===== Load persistent state =====
state = load_state()
now = now_ist()

# ===== Intraday processing =====
if is_market_hours():
    etfs = fetch_all_etfs()
    stocks = fetch_stocks()

    for item in etfs + stocks:

        thresholds = (
            ETF_THRESHOLDS
            if item["id"].startswith("ETF:")
            else STOCK_THRESHOLDS
        )

        # Determine deepest slab crossed
        crossed = None
        for t in sorted(thresholds, reverse=True):
            if item["change"] <= t:
                crossed = t

        if crossed is None:
            continue

        prev = state["alerted"].get(item["id"])

        # Alert only if:
        # - never alerted today
        # - crossed a deeper slab
        if prev is None or prev > crossed:
            send(
                BOT,
                CHAT,
                f"🚨 <b>{item['id']}</b>\n"
                f"Change: {item['change']:.2f}%\n"
                f"Price: ₹{item['price']:.2f}\n"
                f"Slab crossed: {crossed}%"
            )
            state["alerted"][item["id"]] = crossed

# ===== End-of-day summary (once) =====
if now.hour >= 15 and now.minute >= 30 and not state["summary_sent"]:
    send(
        BOT,
        CHAT,
        f"📊 <b>EOD Summary</b>\n"
        f"Total alerts today: {len(state['alerted'])}"
    )
    state["summary_sent"] = True

# ===== Persist state =====
save_state(state)

