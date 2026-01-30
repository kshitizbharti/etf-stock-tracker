import os
from market import is_market_hours, now_ist
from state import load_state, save_state
from notifier import send
from stock_fetcher import fetch_stocks
from etf_fetcher import fetch_all_etfs

BOT = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]

IS_MANUAL = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

STOCK_SLABS = [-5.0, -8.0, -10.0]
ETF_SLABS = [-2.5, -3.5, -5.0, -8.0, -10.0]

now = now_ist()
market_open = is_market_hours()

state = load_state() if not IS_MANUAL else {"alerted": {}}

stocks = fetch_stocks() if market_open else []
etfs = fetch_all_etfs() if market_open else []

# 🔥 ALWAYS DEBUG ON MANUAL RUN
if IS_MANUAL:
    send(
        BOT, CHAT,
        f"🧪 <b>MANUAL DEBUG</b>\n"
        f"Time: {now.strftime('%H:%M:%S')} IST\n"
        f"Market open: {market_open}\n"
        f"Stocks fetched: {len(stocks)}\n"
        f"ETFs fetched: {len(etfs)}"
    )

def process(items, slabs):
    for it in items:
        crossed = None
        for s in slabs:
            if it["change"] <= s:
                crossed = s
        if crossed is None:
            continue

        prev = state["alerted"].get(it["id"])

        if IS_MANUAL or prev is None or crossed < prev:
            send(
                BOT, CHAT,
                f"🚨 <b>{it['id']}</b>\n"
                f"Change: {it['change']:.2f}%\n"
                f"Price: ₹{it['price']:.2f}\n"
                f"Slab: {crossed}%"
            )
            state["alerted"][it["id"]] = crossed

if market_open:
    process(stocks, STOCK_SLABS)
    process(etfs, ETF_SLABS)

if not IS_MANUAL:
    save_state(state)
