
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


    # === POSITION RANKING UI LOGIC ===
    ranked_positions = []

    for p in positions:
        try:
            change = float(p.unrealized_plpc)
            score = 50 + (change * 120)

            if change <= -0.04:
                score -= 30
            elif change <= -0.02:
                score -= 20

            if change >= 0.03:
                score += 15

            ranked_positions.append((p, score))
        except Exception:
            ranked_positions.append((p, 0))

    ranked_positions.sort(key=lambda x: x[1])
    weakest_symbol = ranked_positions[0][0].symbol if ranked_positions else None

    rows = ""
    total_pl = 0

    for p, score in ranked_positions:
        pl = float(p.unrealized_pl)
        total_pl += pl
        color = "green" if pl >= 0 else "red"
        flag = "⚠️" if p.symbol == weakest_symbol else ""

        rows += f"""
        <tr>
            <td>{html.escape(p.symbol)} {flag}</td>
            <td>{p.qty}</td>
            <td>{money(p.avg_entry_price)}</td>
            <td>{money(p.current_price)}</td>
            <td class="{color}">{money(pl)}</td>
            <td class="{color}">{float(p.unrealized_plpc) * 100:.2f}%</td>
            <td>{round(score, 1)}</td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='7'>No open positions</td></tr>"


    # === DASHBOARD INTELLIGENCE LOGIC ===
    decision_keywords = ["BUY", "SELL", "SKIP", "ROTATION", "NO ROTATION", "BUY DECISION"]
    decision_lines = [line.strip() for line in logs if any(k in line for k in decision_keywords)]
    decision_lines = decision_lines[-8:]

    decision_items = ""
    for line in reversed(decision_lines):
        safe_line = html.escape(line)
        decision_items += f"<li>{safe_line}</li>"

    if not decision_items:
        decision_items = "<li>No recent bot decisions yet.</li>"

    sell_count = len([line for line in logs if "SELL |" in line])
    buy_count = len([line for line in logs if "BUY |" in line or "BUY DECISION" in line])
    skip_count = len([line for line in logs if "SKIP BUY" in line])
    rotation_count = len([line for line in logs if "ROTATION APPROVED" in line])

    portfolio_value = float(account.portfolio_value)
    buying_power = float(account.buying_power)
    deployed_value = max(0, portfolio_value - buying_power)
    deployed_pct = (deployed_value / portfolio_value) * 100 if portfolio_value else 0

    open_winners = 0
    open_losers = 0

    for p in positions:
        if float(p.unrealized_pl) >= 0:
            open_winners += 1
        else:
            open_losers += 1

    if open_winners + open_losers > 0:
        open_win_rate = (open_winners / (open_winners + open_losers)) * 100
    else:
        open_win_rate = 0

    ai_feed = []

    if clock.is_open:
        ai_feed.append("Market is open. Bot is actively monitoring candidates.")
    else:
        ai_feed.append("Market is closed. Bot is idle and monitoring only.")

    if weakest_symbol:
        ai_feed.append(f"Weakest current position: {weakest_symbol}. This is the first rotation candidate.")

    if total_pl < 0:
        ai_feed.append("Open portfolio risk is negative. Rotation and exit logic should stay defensive.")
    else:
        ai_feed.append("Open portfolio P/L is positive or flat. Bot can protect gains and wait for better setups.")

    if status_data.get("slots_available", 0) == 0:
        ai_feed.append("No open slots available. New trades require rotation or exits.")
    else:
        ai_feed.append("There are open slots available for new qualified trades.")

    ai_feed_items = ""
    for item in ai_feed:
        ai_feed_items += f"<li>{html.escape(item)}</li>"

    # === PRO DASHBOARD LOGIC V2 ===
    decision_keywords = [
        "BUY", "SELL", "SKIP BUY", "ROTATION", "NO ROTATION",
        "BUY DECISION", "ADAPTIVE", "SCANNER"
    ]

    decision_lines = [
        line.strip() for line in logs
        if any(k in line for k in decision_keywords)
    ][-12:]

    decision_items = ""
    for line in reversed(decision_lines):
        safe_line = html.escape(line)
        decision_items += f"<li>{safe_line}</li>"

    if not decision_items:
        decision_items = "<li>No recent bot decisions yet.</li>"

    buy_count = len([line for line in logs if "BUY |" in line or "BUY DECISION" in line])
    sell_count = len([line for line in logs if "SELL |" in line])
    skip_count = len([line for line in logs if "SKIP BUY" in line])
    rotation_count = len([line for line in logs if "ROTATION APPROVED" in line])
    scanner_count = len([line for line in logs if "SCANNER" in line])
    adaptive_count = len([line for line in logs if "ADAPTIVE" in line])

    portfolio_value = float(account.portfolio_value)
    buying_power = float(account.buying_power)

    position_value = 0
    for p in positions:
        try:
            position_value += abs(float(p.market_value))
        except Exception:
            pass

    deployed_pct = (position_value / portfolio_value) * 100 if portfolio_value else 0

    open_winners = len([p for p in positions if float(p.unrealized_pl) >= 0])
    open_losers = len([p for p in positions if float(p.unrealized_pl) < 0])
    open_total = open_winners + open_losers
    open_win_rate = (open_winners / open_total * 100) if open_total else 0

    weakest_position_name = weakest_symbol if weakest_symbol else "None"

    risk_mode = "Defensive" if total_pl < 0 else "Normal"
    risk_color = "red" if total_pl < 0 else "green"

    slot_status = "Full" if status_data.get("slots_available", 0) == 0 else "Available"
    slot_color = "yellow" if slot_status == "Full" else "green"

    ai_feed = []

    if clock.is_open:
        ai_feed.append("Market is open. Scanner, scoring, risk checks, and rotation logic are active.")
    else:
        ai_feed.append("Market is closed. Bot is online and waiting for the next session.")

    ai_feed.append(f"Weakest position: {weakest_position_name}. This is the first rotation candidate.")
    ai_feed.append(f"Risk mode: {risk_mode}. Open P/L is {money(total_pl)}.")
    ai_feed.append(f"Capital deployed: {deployed_pct:.1f}% across {len(positions)} positions.")
    ai_feed.append(f"Recent engine activity: {buy_count} buys, {sell_count} sells, {skip_count} skips, {rotation_count} rotations.")

    ai_feed_items = ""
    for item in ai_feed:
        ai_feed_items += f"<li>{html.escape(item)}</li>"

    scanner_lines = [line.strip() for line in logs if "SCANNER" in line][-6:]
    scanner_items = ""

    for line in reversed(scanner_lines):
        scanner_items += f"<li>{html.escape(line)}</li>"

    if not scanner_items:
        scanner_items = "<li>No scanner output yet. Scanner will update when market logic runs.</li>"

    adaptive_lines = [line.strip() for line in logs if "ADAPTIVE" in line][-6:]
    adaptive_items = ""

    for line in reversed(adaptive_lines):
        adaptive_items += f"<li>{html.escape(line)}</li>"

    if not adaptive_items:
        adaptive_items = "<li>Adaptive learning is in safe neutral mode until more closed trades are collected.</li>"

    # === PERFORMANCE INTELLIGENCE LOGIC ===
    health_score = 100
    health_notes = []
    health_suggestions = []

    if open_win_rate < 45 and len(positions) > 0:
        health_score -= 20
        health_notes.append("Open win rate is weak.")
        health_suggestions.append("Tighten candidate quality or improve exits before increasing size.")

    if total_pl < 0:
        health_score -= 20
        health_notes.append("Open P/L is negative.")
        health_suggestions.append("Keep rotation defensive and avoid adding weak setups.")

    if scanner_count == 0:
        health_score -= 15
        health_notes.append("Scanner has not produced recent events.")
        health_suggestions.append("Watch scanner logs tomorrow; if still quiet, lower scanner threshold or expand universe.")

    if rotation_count == 0 and status_data.get("slots_available", 0) == 0:
        health_score -= 10
        health_notes.append("No rotations while slots are full.")
        health_suggestions.append("Rotation may need stronger candidate flow before it activates.")

    if adaptive_count == 0:
        health_score -= 5
        health_notes.append("Adaptive learning has not activated yet.")
        health_suggestions.append("Collect more closed trades before enabling factor-level learning.")

    health_score = max(0, min(100, health_score))

    if health_score >= 80:
        health_label = "Strong"
        health_class = "green"
    elif health_score >= 60:
        health_label = "Stable"
        health_class = "yellow"
    else:
        health_label = "Needs Attention"
        health_class = "red"

    if not health_notes:
        health_notes.append("System health looks stable based on current dashboard signals.")

    if not health_suggestions:
        health_suggestions.append("Let the system collect more data before making aggressive changes.")

    health_note_items = ""
    for note in health_notes:
        health_note_items += f"<li>{html.escape(note)}</li>"

    health_suggestion_items = ""
    for suggestion in health_suggestions[:5]:
        health_suggestion_items += f"<li>{html.escape(suggestion)}</li>"
    return f"""
    <html>
    <head>
        <title>Ponder Invest AI</title>
        <meta http-equiv="refresh" content="5">
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background:
                    radial-gradient(circle at top left, rgba(0,255,136,0.14), transparent 28%),
                    radial-gradient(circle at top right, rgba(59,130,246,0.16), transparent 30%),
                    #030712;
                color: #f8fafc;
            }}

            .container {{
                max-width: 1400px;
                margin: auto;
                padding: 24px;
            }}

            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 18px;
                margin-bottom: 22px;
            }}

            .brand {{
                font-size: 38px;
                font-weight: 900;
                letter-spacing: -1.2px;
            }}

            .brand span {{ color: #00ff88; }}

            .subtitle {{
                color: #94a3b8;
                margin-top: 6px;
            }}

            .pill {{
                padding: 10px 16px;
                border-radius: 999px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                font-weight: 900;
                white-space: nowrap;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
                gap: 16px;
                margin-bottom: 16px;
            }}

            .grid-2 {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
                gap: 16px;
                margin-bottom: 16px;
            }}

            .card {{
                background: rgba(15, 23, 42, 0.86);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 22px;
                padding: 20px;
                box-shadow: 0 20px 45px rgba(0,0,0,0.35);
                margin-bottom: 16px;
            }}

            .card h2, .card h3 {{
                margin-top: 0;
                margin-bottom: 12px;
            }}

            .big {{
                font-size: 30px;
                font-weight: 900;
                letter-spacing: -0.5px;
            }}

            .small {{
                font-size: 13px;
            }}

            .green {{ color: #00ff88; }}
            .red {{ color: #ff5c7a; }}
            .yellow {{ color: #ffd84d; }}
            .blue {{ color: #60a5fa; }}
            .muted {{ color: #94a3b8; }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                color: #94a3b8;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}

            th, td {{
                padding: 13px 10px;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                text-align: left;
            }}

            tr:hover {{ background: rgba(255,255,255,0.04); }}

            pre {{
                background: #020617;
                padding: 16px;
                border-radius: 16px;
                overflow: auto;
                max-height: 300px;
                color: #d1d5db;
                border: 1px solid rgba(255,255,255,0.08);
            }}

            ul {{
                margin: 0;
                padding-left: 18px;
            }}

            li {{
                margin-bottom: 8px;
                line-height: 1.35;
            }}

            .status-row {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 10px;
            }}

            .mini-pill {{
                padding: 7px 11px;
                border-radius: 999px;
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.09);
                font-weight: 700;
                font-size: 13px;
            }}

            .footer {{
                color: #64748b;
                text-align: center;
                padding: 18px;
            }}

            @media (max-width: 700px) {{
                .container {{ padding: 14px; }}
                .header {{ flex-direction: column; align-items: flex-start; }}
                .brand {{ font-size: 30px; }}
                .big {{ font-size: 24px; }}
                th, td {{ padding: 10px 6px; font-size: 12px; }}
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <div class="header">
                <div>
                    <div class="brand">Ponder Invest <span>AI</span></div>
                    <div class="subtitle">Advanced autonomous paper-trading command center · refreshes every 5 seconds</div>
                    <div class="status-row">
                        <span class="mini-pill {risk_color}">Risk Mode: {risk_mode}</span>
                        <span class="mini-pill {slot_color}">Slots: {slot_status}</span>
                        <span class="mini-pill blue">Weakest: {weakest_position_name}</span>
                    </div>
                </div>
                <div class="pill {status_class}">{bot_status}</div>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>Account Status</h3>
                    <div class="big">{account.status}</div>
                    <p class="muted">Connected to Alpaca paper trading</p>
                </div>

                <div class="card">
                    <h3>Portfolio Value</h3>
                    <div class="big">{money(account.portfolio_value)}</div>
                    <p class="muted">Total account value</p>
                </div>

                <div class="card">
                    <h3>Buying Power</h3>
                    <div class="big">{money(account.buying_power)}</div>
                    <p class="muted">Available deployable capital</p>
                </div>

                <div class="card">
                    <h3>Open P/L</h3>
                    <div class="big {'green' if total_pl >= 0 else 'red'}">{money(total_pl)}</div>
                    <p class="muted">Unrealized position P/L</p>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>Open Win Rate</h3>
                    <div class="big">{open_win_rate:.1f}%</div>
                    <p class="muted">{open_winners} winners · {open_losers} losers</p>
                </div>

                <div class="card">
                    <h3>Capital Deployed</h3>
                    <div class="big">{deployed_pct:.1f}%</div>
                    <p class="muted">{money(position_value)} currently deployed</p>
                </div>

                <div class="card">
                    <h3>Bot Actions</h3>
                    <div class="big">{buy_count + sell_count + skip_count}</div>
                    <p class="muted">Buys {buy_count} · Sells {sell_count} · Skips {skip_count}</p>
                </div>

                <div class="card">
                    <h3>Rotations</h3>
                    <div class="big">{rotation_count}</div>
                    <p class="muted">Approved rotation events in recent logs</p>
                </div>

                <div class="card">
                    <h3>Scanner Events</h3>
                    <div class="big">{scanner_count}</div>
                    <p class="muted">Recent candidate scan activity</p>
                </div>

                <div class="card">
                    <h3>Adaptive Events</h3>
                    <div class="big">{adaptive_count}</div>
                    <p class="muted">Learning adjustments logged</p>
                </div>
            </div>

            <div class="card">
                <h2>AI Market Summary</h2>
                <p><b>Market:</b> {summary.get("market_summary", "No market summary yet.")}</p>
                <p><b>Opportunities:</b> {summary.get("opportunity_summary", "No opportunity summary yet.")}</p>
                <p><b>Risk:</b> {summary.get("risk_summary", "No risk summary yet.")}</p>
                <p class="muted">{summary.get("full_summary", "")}</p>
            </div>

            <div class="grid-2">
                <div class="card">
                    <h3>Live Decision Panel</h3>
                    <ul>{decision_items}</ul>
                </div>

                <div class="card">
                    <h3>AI Reasoning Feed</h3>
                    <ul>{ai_feed_items}</ul>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <h3>Scanner Intelligence</h3>
                    <ul>{scanner_items}</ul>
                </div>

                <div class="card">
                    <h3>Adaptive Learning Feed</h3>
                    <ul>{adaptive_items}</ul>
                </div>
            </div>

            <div class="grid-2">
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
                <h2>Performance Intelligence</h2>
                <div class="grid">
                    <div>
                        <h3>System Health</h3>
                        <div class="big {health_class}">{health_score}/100</div>
                        <p class="muted">{health_label}</p>
                    </div>
                    <div>
                        <h3>Detected Issues</h3>
                        <ul>{health_note_items}</ul>
                    </div>
                    <div>
                        <h3>Suggested Actions</h3>
                        <ul>{health_suggestion_items}</ul>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Position Ranking</h2>
                <p class="muted">Weakest position is marked with ⚠️. Lower score means weaker holding.</p>
                <table>
                    <tr>
                        <th>Symbol</th>
                        <th>Qty</th>
                        <th>Entry</th>
                        <th>Current</th>
                        <th>P/L $</th>
                        <th>P/L %</th>
                        <th>Score</th>
                    </tr>
                    {rows}
                </table>
            </div>

            <div class="card">
                <h2>Recent Bot Logs</h2>
                <pre>{escaped_logs}</pre>
            </div>

            <div class="footer">
                Ponder Invest AI · Adaptive cloud trading dashboard
            </div>

        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
