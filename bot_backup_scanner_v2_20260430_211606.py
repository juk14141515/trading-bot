import time
from datetime import datetime
import requests
import alpaca_trade_api as tradeapi
import yfinance as yf
import os
import json

def update_status(data):
    try:
        with open("bot_status.json", "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Status write error:", e)

from dotenv import load_dotenv
from scoring_engine import calculate_weighted_score
from volatility import get_atr, calculate_position_size
from small_cap_scanner import get_small_cap_candidates
from rotation_manager import find_weakest_position, should_rotate
from exit_manager import should_exit
from enhanced_scanner import get_enhanced_candidates

from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

from backtest import run_backtest
from risk_manager import can_trade
from trade_memory import record_trade
from adaptive_learning import apply_adaptive_score, get_performance_summary

# ===== SETTINGS =====
MAX_DAILY_LOSS_PERCENT = 0.02
START_OF_DAY_EQUITY = None
TRADING_HALTED = False

load_dotenv()

API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL")

strategy = run_backtest()
print(f"Using strategy: {strategy}")

FINNHUB_API_KEY = "d7ntn5hr01qs975tf2r0d7ntn5hr01qs975tf2rg"

WATCHLIST = [
    "AAPL", "AMZN", "NVDA", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "PLTR", "SOFI",
    "COIN", "RBLX", "U",
    "NFLX", "ORCL", "UBER", "SHOP", "PYPL",
    "SQ", "HOOD", "AFRM",
    "NET", "DDOG", "CRWD", "PANW", "ZS",
    "MDB", "APP", "UPST",
    "DKNG", "ROKU",
    "F", "GM", "T", "DIS"
]

PAPER_ACCOUNT_SIZE = 200000

MAX_TOTAL_DEPLOYED_PERCENT = 0.30
MAX_SINGLE_TRADE_PERCENT = 0.08
MIN_TRADE_DOLLARS = 500

STOP_LOSS_PERCENT = 0.06
TAKE_PROFIT_PERCENT = 0.12
MAX_POSITIONS = 3

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)
news_client = NewsClient(api_key=API_KEY, secret_key=SECRET_KEY)

last_buy_day = None


def log(message):
    with open("log.txt", "a") as f:
        f.write(f"{datetime.now()} | {message}\n")
def notify_discord(message):
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        log("DISCORD | missing webhook url")
        return

    try:
        requests.post(url, json={"content": message}, timeout=10)
    except Exception as e:
        log(f"DISCORD | failed | {e}")

def market_is_open():
    try:
        clock = api.get_clock()
        return clock.is_open
    except Exception as e:
        print(f"ERROR | market clock | {e}")
        return False


def get_positions():
    return api.list_positions()


def already_holding(symbol):
    return any(p.symbol == symbol for p in get_positions())


def calculate_trade_dollars(score):
    account = api.get_account()
    buying_power = float(account.buying_power)

    if score >= 50:
        dollars = buying_power * 0.08
    elif score >= 35:
        dollars = buying_power * 0.06
    elif score >= 20:
        dollars = buying_power * 0.04
    elif score >= 10:
        dollars = buying_power * 0.025
    else:
        dollars = MIN_TRADE_DOLLARS

    max_single_trade = buying_power * MAX_SINGLE_TRADE_PERCENT

    dollars = min(dollars, max_single_trade)
    dollars = max(dollars, MIN_TRADE_DOLLARS)

    return round(dollars, 2)

def get_deployed_value():
    total = 0

    for p in get_positions():
        total += float(p.market_value)

    return total


def get_trend(symbol):
    data = yf.download(symbol, period="6mo", interval="1d", auto_adjust=True, progress=False)

    if data.empty:
        return "bad_data"

    data["SMA20"] = data["Close"].rolling(20).mean()
    data["SMA50"] = data["Close"].rolling(50).mean()

    latest = data.iloc[-1]

    close = float(latest["Close"])
    sma20 = float(latest["SMA20"])
    sma50 = float(latest["SMA50"])

    if close > sma20 > sma50:
        return "bullish"
    elif close < sma20 < sma50:
        return "bearish"
    else:
        return "neutral"


def finnhub_analyst_score(symbol):
    try:
        url = "https://finnhub.io/api/v1/stock/recommendation"
        params = {"symbol": symbol, "token": FINNHUB_API_KEY}

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data:
            log(f"{symbol} | analyst_score=0 | no Finnhub data")
            return 0

        latest = data[-1]

        strong_buy = latest.get("strongBuy", 0)
        buy = latest.get("buy", 0)
        sell = latest.get("sell", 0)
        strong_sell = latest.get("strongSell", 0)

        score = (strong_buy * 2) + buy - sell - (strong_sell * 2)

        log(f"{symbol} | analyst_score={score}")
        return score

    except Exception as e:
        log(f"ERROR | finnhub {symbol} | {e}")
        return 0


def news_score(symbol):
    try:
        request = NewsRequest(symbols=symbol, limit=10)
        news = news_client.get_news(request)

        if not news:
            log(f"{symbol} | news_score=0 | no news")
            return 0

        bullish_words = [
            "beat", "growth", "surge", "rally", "upgrade",
            "raises", "record", "profit", "strong", "ai"
        ]

        bearish_words = [
            "miss", "lawsuit", "downgrade", "falls",
            "drop", "weak", "loss", "cuts"
        ]

        score = 0

        for article in news:
            headline = article.headline.lower()

            for word in bullish_words:
                if word in headline:
                    score += 1

            for word in bearish_words:
                if word in headline:
                    score -= 1

        log(f"{symbol} | news_score={score}")
        return score

    except Exception as e:
        log(f"ERROR | news {symbol} | {e}")
        return 0



def buy(symbol, score):
    price = float(api.get_latest_trade(symbol).price)

    atr = get_atr(symbol)

    shares = calculate_position_size(
        account_equity=float(api.get_account().equity),
        risk_percent=0.01,
        entry_price=price,
        atr=atr,
        atr_multiplier=2
    )

    if shares <= 0:
        log(f"SKIP BUY | {symbol} | invalid position size")
        return

    dollars = shares * price

    deployed = get_deployed_value()
    account = api.get_account()
    equity = float(account.equity)

    max_deployed = equity * MAX_TOTAL_DEPLOYED_PERCENT

    if deployed + dollars > max_deployed:
        log(f"SKIP BUY | {symbol} | would exceed max deployed")
        return

    log(f"BUY {symbol} | price={price:.2f} | ATR={atr} | shares={shares} | dollars={dollars:.2f}")

    api.submit_order(
        symbol=symbol,
        notional=dollars,
        side="buy",
        type="market",
        time_in_force="day"
    )

    print(f"BUY placed: {symbol} | ${dollars}")
    log(f"BUY | {symbol} | dollars={dollars:.2f} | score={score} | reason=order submitted")
    notify_discord(f"🟢 BUY PLACED | {symbol} | ${dollars:.2f} | score={score}")

    try:
        record_trade(symbol, "buy", shares, price, reason="buy order submitted", score=score)
    except Exception as e:
        log(f"TRADE MEMORY ERROR | buy {symbol} | {e}")

def sell(symbol, qty, reason):
    sell_price = None
    pnl = None
    pnl_pct = None

    try:
        sell_price = float(api.get_latest_trade(symbol).price)
        for pos in get_positions():
            if pos.symbol == symbol:
                entry = float(pos.avg_entry_price)
                pnl = (sell_price - entry) * float(qty)
                pnl_pct = (sell_price - entry) / entry
                break
    except Exception as e:
        log(f"TRADE MEMORY ERROR | pre-sell calc {symbol} | {e}")

    api.submit_order(
        symbol=symbol,
        qty=qty,
        side="sell",
        type="market",
        time_in_force="day"
    )

    print(f"SELL placed: {symbol} | {reason}")
    log(f"SELL | {symbol} | reason={reason} | pnl={pnl} | pnl_pct={pnl_pct}")
    notify_discord(f"🔴 SELL PLACED | {symbol} | qty={qty} | reason={reason}")

    try:
        record_trade(symbol, "sell", qty, sell_price, reason=reason, score=None, pnl=pnl, pnl_pct=pnl_pct)
    except Exception as e:
        log(f"TRADE MEMORY ERROR | sell {symbol} | {e}")


def manage_existing_positions():
    positions = get_positions()

    for p in positions:
        symbol = p.symbol
        qty = abs(float(p.qty))
        entry = float(p.avg_entry_price)
        current = float(p.current_price)

        change = (current - entry) / entry

        log(f"P/L | {symbol} | {change:.2%}")

        if change <= -STOP_LOSS_PERCENT:
            sell(symbol, qty, "stop loss")

        elif change >= TAKE_PROFIT_PERCENT:
            sell(symbol, qty, "take profit")

        elif get_trend(symbol) == "bearish":
            sell(symbol, qty, "trend bearish")

        else:
            exit_now, reason = should_exit(p, get_trend)
            if exit_now:
                sell(symbol, qty, reason)

def daily_loss_check():
    global START_OF_DAY_EQUITY, TRADING_HALTED

    account = api.get_account()
    current_equity = float(account.equity)

    # Set start of day equity once
    if START_OF_DAY_EQUITY is None:
        START_OF_DAY_EQUITY = current_equity
        log(f"START DAY EQUITY | ${START_OF_DAY_EQUITY:.2f}")
        return True

    if START_OF_DAY_EQUITY == 0:
        return True

    loss_percent = (START_OF_DAY_EQUITY - current_equity) / START_OF_DAY_EQUITY

    log(f"DAILY LOSS CHECK | start=${START_OF_DAY_EQUITY:.2f} | current=${current_equity:.2f} | loss={loss_percent:.2%}")

    if loss_percent >= MAX_DAILY_LOSS_PERCENT:
        TRADING_HALTED = True
        log("TRADING HALTED | Max daily loss reached")
        print("🚨 TRADING HALTED: Max daily loss reached")
        return False

    return True

def run_bot():
    global last_buy_day

    print("\n--- Bot cycle ---")
    log("NEW CYCLE")

    if not market_is_open():
        log("SKIP BUY | market closed")

        update_status({
            "market_trend": "closed",
            "watchlist": [],
            "top_candidates": [],
            "positions": len(get_positions()),
            "slots_available": 0,
            "summary": {
                "market_summary": "Market is currently closed.",
                "opportunity_summary": "No trading opportunities while market is closed.",
                "risk_summary": "No new trade risk while bot is idle.",
                "watchlist_summary": "Scanner will resume when the market opens.",
                "full_summary": "Market closed. Bot is online, idle, and waiting for the next trading session."
            }
        })

        return

    # Manage open positions first
    manage_existing_positions()

    if TRADING_HALTED:
        log("SKIP BUY | trading halted for today")
        return

    if not daily_loss_check():
        return

    today = datetime.now().date()
    log("TRADE FREQUENCY | multi-trade mode active | daily cap controlled by risk manager")

    # Buy logic can run multiple times per day.
    # Daily trade count is controlled by risk_manager.py.

    market_trend = get_trend("SPY")
    log(f"SPY trend={market_trend}")

    if market_trend != "bullish":
        log("SKIP BUY | SPY not bullish")
        return

    positions = get_positions()
    current_positions = len(positions)
    slots_available = MAX_POSITIONS - current_positions
    rotation_mode = False
    weakest_position = None

    if slots_available <= 0:
        weakest_position = find_weakest_position(positions)
        rotation_mode = True
        log(f"ROTATION CHECK | max positions reached | weakest={weakest_position}")
        slots_available = 1

    candidates = []

    try:
        small_caps = get_small_cap_candidates()
        enhanced = get_enhanced_candidates()
        small_caps = list(set(small_caps + enhanced))
    except Exception as e:
        log(f"Small-cap scanner error: {e}")
        small_caps = []

    dynamic_watchlist = list(dict.fromkeys(WATCHLIST + small_caps))
    log(f"Dynamic watchlist: {dynamic_watchlist}")

    for symbol in dynamic_watchlist:
        if symbol == "SPY":
            continue

        if already_holding(symbol):
            continue

        trend = get_trend(symbol)
        analyst = finnhub_analyst_score(symbol)
        news = news_score(symbol)

        trend_score = 100 if trend == "bullish" else 0

        total = calculate_weighted_score(
            trend_score=trend_score,
            analyst_score=analyst * 10,
            news_score=max(0, min(100, news * 10)),
            momentum_score=get_momentum_score(symbol),
            volatility_score=50,
        )

        log(f"{symbol} | trend={trend} | analyst={analyst} | news={news} | total={total}")

        if trend == "bullish" and analyst >= 3 and news >= 0:
            candidates.append((symbol, total))

    candidates.sort(key=lambda x: x[1], reverse=True)

    for symbol, score in candidates[:slots_available]:
        final_score, adaptive_reason = apply_adaptive_score(symbol, score)
        log(f"ADAPTIVE | {symbol} | {adaptive_reason}")

        if rotation_mode:
            rotate_ok, rotate_reason = should_rotate(weakest_position, final_score)
            if not rotate_ok:
                log(f"NO ROTATION | candidate={symbol} | reason={rotate_reason}")
                continue

            log(f"ROTATION APPROVED | replacing={weakest_position['symbol']} | new={symbol} | score={final_score} | reason={rotate_reason}")
            sell(weakest_position["symbol"], weakest_position["qty"], f"rotation into {symbol}")
            notify_discord(f"🔁 ROTATION | Sold {weakest_position['symbol']} to buy {symbol} | score={final_score}")
            return

        allowed, reason = can_trade(symbol, final_score)
        if not allowed:
            log(f"SKIP BUY | {symbol} | {reason}")
            notify_discord(f"⏩ SKIP BUY | {symbol} | {reason}")
            continue

        log(f"BUY DECISION | {symbol} | score={final_score} | reason=qualified candidate passed risk checks")
        buy(symbol, final_score)
        update_status({
             "last_action": f"BUY {symbol}",
             "last_score": final_score
})

    last_buy_day = today


print("AI trading bot running every 5 minutes...")
notify_discord("✅ AI trading bot started/restarted and is running.")

while True:
    try:
        run_bot()
    except Exception as e:
        print("Bot error:", e)
        log(f"ERROR | {e}")
        notify_discord(f"🚨 BOT ERROR | {e}")

    time.sleep(300)
