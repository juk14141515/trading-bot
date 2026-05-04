from learning_shadow import log_learning_event
from shadow_learning_v2 import run_shadow_learning_v2
import time
from datetime import datetime
import requests
import alpaca_trade_api as tradeapi
import yfinance as yf
import os
import json


def load_bot_status():
    try:
        if os.path.exists("bot_status.json"):
            with open("bot_status.json", "r") as f:
                return json.load(f)
    except Exception as e:
        print("Status read error:", e)
    return {}


def update_status(data):
    try:
        with open("bot_status.json", "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Status write error:", e)


def set_why_not_trading(reason, detail="", state="waiting"):
    status = load_bot_status()
    status.update({
        "why_not_trading": reason,
        "last_skip_reason": detail or reason,
        "trading_state": state,
        "status_updated_at": datetime.now().isoformat(timespec="seconds"),
    })
    update_status(status)

from dotenv import load_dotenv
from scoring_engine import calculate_weighted_score
from volatility import get_atr, calculate_position_size
from small_cap_scanner import get_small_cap_candidates
from rotation_manager import find_weakest_position, should_rotate
from trade_guard_v1 import should_force_exit
from rotation_tuner_v1 import approve_rotation
from exit_manager import should_exit
from enhanced_scanner import get_enhanced_candidates

from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

from backtest import run_backtest
from risk_manager import can_trade
from trade_memory import record_trade
from adaptive_learning import apply_adaptive_score, get_performance_summary, get_win_loss_summary
from metrics_tracker import record_equity_snapshot
from push_alerts import important_alert

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

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

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

ALERT_CACHE = {}


def log(message):
    with open("log.txt", "a") as f:
        f.write(f"{datetime.now()} | {message}\n")

def notify_discord(message):
    url = os.getenv("DISCORD_WEBHOOK_URL")

    try:
        priority = "default"
        tags = "chart_with_upwards_trend"

        upper_msg = str(message).upper()

        if "BOT ERROR" in upper_msg or "STOP_TRADING" in upper_msg or "EMERGENCY" in upper_msg:
            priority = "urgent"
            tags = "rotating_light"
        elif "BUY" in upper_msg:
            priority = "high"
            tags = "moneybag"
        elif "SELL" in upper_msg:
            priority = "high"
            tags = "warning"
        elif "ROTATION" in upper_msg:
            priority = "high"
            tags = "twisted_rightwards_arrows"
        elif "WEAK POSITION" in upper_msg:
            priority = "high"
            tags = "warning"
        elif "SCANNER" in upper_msg:
            priority = "default"
            tags = "mag"

        important_alert("Ponder Invest AI", message, priority, tags)

    except Exception as e:
        try:
            log(f"PUSH | failed | {e}")
        except Exception:
            pass

    if not url:
        log("DISCORD | missing webhook url")
        return

    try:
        requests.post(url, json={"content": message}, timeout=5)
    except Exception as e:
        log(f"DISCORD | failed | {e}")


def alert_once(key, message, cooldown_seconds=1800):
    now = time.time()
    last = ALERT_CACHE.get(key, 0)

    if now - last >= cooldown_seconds:
        ALERT_CACHE[key] = now
        notify_discord(message)


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

# ... (rest unchanged up to candidates.sort)

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

    # --- SHADOW LEARNING V2 (RESEARCH ONLY) ---
    try:
        run_shadow_learning_v2(
            positions=get_positions(),
            candidates=candidates,
            log_func=log
        )
    except Exception as e:
        log(f"SHADOW V2 ERROR | {e}")

    if len(candidates) == 0 and enhanced:
        log(f"LEARNING MODE | no scored candidates | using enhanced fallback={enhanced[:2]}")
        for fallback_symbol in enhanced[:2]:
            candidates.append({"symbol": fallback_symbol, "score": 65, "trend": "enhanced_fallback", "analyst": 0, "news": 0})

# (rest of file unchanged)
