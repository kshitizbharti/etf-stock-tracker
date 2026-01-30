from state import load_state, save_state
from market import is_market_hours, now_ist
from upstox_scraper import fetch_all_etfs
from stock_fetcher import fetch_stocks
from notifier import send
import os

ETF_THRESHOLDS = [-2.5, -3.5, -5.0, -8.0, -10.0]
STOCK_THRESHOLDS = [-5.0, -8.0, -10.0]

BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

state = load_state()
now = now_ist()

# INTRADAY
if is_market_hours():
    etfs = fetch_all_etfs()
    stocks = fetch_stocks()

    for item in etfs + stocks:
        thresholds = ETF_THRESHOLDS if item["id"].startswith("ETF:") else [STOCK_THRESHOLD]

        for t in thresholds:
            if item["change"] <= t:
                prev = state["alerted"].get(item["id"])
                if prev is None or prev > t:
                    send(
                        BOT,
                        CHAT,
                        f"🚨 <b>{item['id']}</b>\n"
                        f"Change: {item['change']:.2f}%\n"
                        f"Price: ₹{item['price']:.2f}"
                    )
                    state["alerted"][item["id"]] = t

# EOD SUMMARY (ONCE)
if now.hour >= 15 and now.minute >= 30 and not state["summary_sent"]:
    send(
        BOT,
        CHAT,
        f"📊 <b>EOD Summary</b>\n"
        f"Total alerts today: {len(state['alerted'])}"
    )
    state["summary_sent"] = True

save_state(state)

