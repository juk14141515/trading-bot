import time
from datetime import datetime
import requests
import alpaca_trade_api as tradeapi
import yfinance as yf
import os
from dotenv import load_dotenv

from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

from backtest import run_backtest

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
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "AMZN", "META", "TSLA",
    "PLTR", "SNOW", "CRM", "ADBE", "INTC", "SMCI", "AVGO",
    "QCOM", "TXN", "ASML", "AMAT", "MU",
    "SPY", "QQQ", "IWM",
    "JPM", "BAC", "GS", "MS",
    "LLY", "JNJ", "PFE", "MRNA",
    "COST", "WMT", "HD", "NKE",
    "XOM", "CVX",
    "COIN", "RBLX", "U", "SOFI"
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
    dollars = calculate_trade_dollars(score)

    deployed = get_deployed_value()
    account = api.get_account()
    equity = float(account.equity)

    max_deployed = equity * MAX_TOTAL_DEPLOYED_PERCENT

    if deployed + dollars > max_deployed:
        log(f"SKIP BUY | {symbol} | would exceed max deployed | deployed=${deployed:.2f}")
        return

    api.submit_order(
        symbol=symbol,
        notional=dollars,
        side="buy",
        type="market",
        time_in_force="day"
    )

    print(f"BUY placed: {symbol} | ${dollars} | score={score}")
    log(f"BUY | {symbol} | dollars=${dollars} | score={score}")
    notify_discord(f"🟢 BUY PLACED | {symbol} | ${dollars:.2f} | score={score}")
def sell(symbol, qty, reason):
    api.submit_order(
        symbol=symbol,
        qty=qty,
        side="sell",
        type="market",
        time_in_force="day"
    )

    print(f"SELL placed: {symbol} | {reason}")
    log(f"SELL | {symbol} | {reason}")
    notify_discord(f"🔴 SELL PLACED | {symbol} | qty={qty} | reason={reason}")


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
        log("Market closed")
        return

    # Manage open positions first
    manage_existing_positions()

    if TRADING_HALTED:
        log("Trading halted for today")
        return

    if not daily_loss_check():
        return

    today = datetime.now().date()

    if last_buy_day == today:
        log("Buy logic skipped | already ran today")
        return

    market_trend = get_trend("SPY")
    log(f"SPY trend={market_trend}")

    if market_trend != "bullish":
        log("No buys | SPY not bullish")
        return

    current_positions = len(get_positions())
    slots_available = MAX_POSITIONS - current_positions

    if slots_available <= 0:
        log("No buys | max positions reached")
        return

    candidates = []

    for symbol in WATCHLIST:
        if symbol == "SPY":
            continue

        if already_holding(symbol):
            continue

        trend = get_trend(symbol)
        analyst = finnhub_analyst_score(symbol)
        news = news_score(symbol)

        total = analyst + news

        log(f"{symbol} | trend={trend} | analyst={analyst} | news={news} | total={total}")

        if trend == "bullish" and analyst >= 3 and news >= 0:
            candidates.append((symbol, total))

    candidates.sort(key=lambda x: x[1], reverse=True)

    for symbol, score in candidates[:slots_available]:
        dollars = calculate_trade_dollars(score)
        log(f"BUY DECISION | {symbol} | score={score} | dollars=${dollars}")
        buy(symbol, score)

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
