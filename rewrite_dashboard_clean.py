import shutil
import subprocess
from datetime import datetime

TARGET = "web_dashboard.py"

backup = f"{TARGET}.backup_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(TARGET, backup)
print(f"Backup created: {backup}")

code = r'''
import os
import json
import html
from functools import wraps

from flask import Flask, request, Response
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL")

DASHBOARD_USER = os.getenv("DASHBOARD_USER")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS")

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version="v2")


def check_auth(username, password):
    if not DASHBOARD_USER or not DASHBOARD_PASS:
        return True
    return username == DASHBOARD_USER and password == DASHBOARD_PASS


def requires_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Login required",
                401,
                {"WWW-Authenticate": 'Basic realm="AI Trading Bot Dashboard"'}
            )
        return func(*args, **kwargs)
    return wrapper


def load_bot_status():
    try:
        with open("bot_status.json", "r") as f:
            return json.load(f)
    except Exception:
        return {}


def read_logs():
    try:
        with open("log.txt", "r") as f:
            return f.readlines()[-30:]
    except Exception:
        return ["No logs yet."]


def money(value):
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "$0.00"


@app.route("/")
@requires_auth
def dashboard():
    account = api.get_account()
    clock = api.get_clock()
    positions = api.list_positions()
    logs = read_logs()

    status_data = load_bot_status()
    summary = status_data.get("summary", {})

    total_pl = 0
    rows = ""

    for p in positions:
        pl = float(p.unrealized_pl)
        total_pl += pl
        color = "green" if pl >= 0 else "red"

        rows += f"""
        <tr>
            <td>{html.escape(p.symbol)}</td>
            <td>{p.qty}</td>
            <td>{money(p.avg_entry_price)}</td>
            <td>{money(p.current_price)}</td>
            <td class="{color}">{money(pl)}</td>
            <td class="{color}">{float(p.unrealized_plpc) * 100:.2f}%</td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='6'>No open positions</td></tr>"

    bot_status = "MARKET OPEN" if clock.is_open else "MARKET CLOSED"
    status_class = "green" if clock.is_open else "yellow"

    escaped_logs = html.escape("".join(logs))

    candidates = status_data.get("top_candidates", [])
    watchlist = status_data.get("watchlist", [])

    candidate_items = ""
    for item in candidates:
        candidate_items += f"<li>{html.escape(str(item))}</li>"

    if not candidate_items:
        candidate_items = "<li>No candidates yet.</li>"

    return f"""
    <html>
    <head>
        <title>AI Trading Bot Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #050505;
                color: white;
            }}
            .container {{
                padding: 25px;
                max-width: 1200px;
                margin: auto;
            }}
            h1 {{
                font-size: 34px;
                margin-bottom: 5px;
            }}
            .subtitle {{
                color: #888;
                margin-bottom: 25px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 18px;
                margin-bottom: 18px;
            }}
            .card {{
                background: #111;
                border: 1px solid #222;
                border-radius: 18px;
                padding: 22px;
                box-shadow: 0 0 20px rgba(0,0,0,0.4);
                margin-bottom: 18px;
            }}
            .big {{
                font-size: 28px;
                font-weight: bold;
            }}
            .green {{ color: #00ff88; }}
            .red {{ color: #ff4d4d; }}
            .yellow {{ color: #ffd84d; }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                border-bottom: 1px solid #222;
                text-align: left;
            }}
            pre {{
                background: #050505;
                padding: 15px;
                border-radius: 12px;
                overflow: auto;
                max-height: 260px;
            }}
            .pill {{
                display: inline-block;
                padding: 8px 14px;
                border-radius: 999px;
                background: #171717;
                font-weight: bold;
            }}
            .muted {{
                color: #aaa;
            }}
            ul {{
                margin: 0;
                padding-left: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI Trading Bot</h1>
            <div class="subtitle">Live cloud dashboard · auto-refreshes every 10 seconds</div>

            <div class="grid">
                <div class="card">
                    <h3>Status</h3>
                    <div class="pill {status_class}">{bot_status}</div>
                    <p>Account: {account.status}</p>
                </div>

                <div class="card">
                    <h3>Portfolio Value</h3>
                    <div class="big">{money(account.portfolio_value)}</div>
                </div>

                <div class="card">
                    <h3>Buying Power</h3>
                    <div class="big">{money(account.buying_power)}</div>
                </div>

                <div class="card">
                    <h3>Open P/L</h3>
                    <div class="big {'green' if total_pl >= 0 else 'red'}">{money(total_pl)}</div>
                </div>
            </div>

            <div class="card">
                <h2>AI Market Summary</h2>
                <p><b>Market:</b> {summary.get("market_summary", "No market summary yet.")}</p>
                <p><b>Opportunities:</b> {summary.get("opportunity_summary", "No opportunity summary yet.")}</p>
                <p><b>Risk:</b> {summary.get("risk_summary", "No risk summary yet.")}</p>
                <p class="muted">{summary.get("full_summary", "")}</p>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>Top Candidates</h3>
                    <ul>{candidate_items}</ul>
                </div>

                <div class="card">
                    <h3>Bot Intelligence</h3>
                    <p><b>Market Trend:</b> {status_data.get("market_trend", "N/A")}</p>
                    <p><b>Positions:</b> {status_data.get("positions", "N/A")}</p>
                    <p><b>Slots Available:</b> {status_data.get("slots_available", "N/A")}</p>
                    <p><b>Watchlist Size:</b> {len(watchlist)}</p>
                    <p><b>Last Action:</b> {status_data.get("last_action", "None")}</p>
                </div>
            </div>

            <div class="card">
                <h2>Open Positions</h2>
                <table>
                    <tr>
                        <th>Symbol</th>
                        <th>Qty</th>
                        <th>Entry</th>
                        <th>Current</th>
                        <th>P/L $</th>
                        <th>P/L %</th>
                    </tr>
                    {rows}
                </table>
            </div>

            <div class="card">
                <h2>Recent Bot Logs</h2>
                <pre>{escaped_logs}</pre>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
'''

with open(TARGET, "w") as f:
    f.write(code)

result = subprocess.run(["python3", "-m", "py_compile", TARGET])

if result.returncode != 0:
    print("Compile failed. Restoring backup.")
    shutil.copy(backup, TARGET)
    raise SystemExit(1)

print("Clean dashboard rewrite complete.")
