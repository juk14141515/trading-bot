from pathlib import Path
from datetime import datetime

BOT = Path("bot.py")
WEB = Path("web_dashboard.py")

bot = BOT.read_text()
web = WEB.read_text()

bot_backup = Path(f"bot_backup_qol_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
web_backup = Path(f"web_dashboard_backup_qol_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")

bot_backup.write_text(bot)
web_backup.write_text(web)

Path("metrics_tracker.py").write_text(r'''
import csv
import os
from datetime import datetime

EQUITY_FILE = "equity_history.csv"
TRADE_FILE = "trade_history.csv"

def record_equity_snapshot(portfolio_value, buying_power, open_pl=0):
    file_exists = os.path.exists(EQUITY_FILE)

    with open(EQUITY_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "portfolio_value", "buying_power", "open_pl"
        ])

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": portfolio_value,
            "buying_power": buying_power,
            "open_pl": open_pl,
        })
''')

# import tracker
if "from metrics_tracker import record_equity_snapshot" not in bot:
    bot = bot.replace(
        "from adaptive_learning import apply_adaptive_score, get_performance_summary",
        "from adaptive_learning import apply_adaptive_score, get_performance_summary\nfrom metrics_tracker import record_equity_snapshot"
    )

# add kill switch + equity snapshot after NEW CYCLE
old = '''    log("NEW CYCLE")
'''

new = '''    log("NEW CYCLE")

    if os.path.exists("STOP_TRADING"):
        log("EMERGENCY STOP ACTIVE | STOP_TRADING file exists")
        notify_discord("🚨 STOP_TRADING active | bot will not place new trades")
        return

    try:
        account_snapshot = api.get_account()
        open_pl_snapshot = 0
        for p in get_positions():
            open_pl_snapshot += float(p.unrealized_pl)

        record_equity_snapshot(
            portfolio_value=float(account_snapshot.portfolio_value),
            buying_power=float(account_snapshot.buying_power),
            open_pl=open_pl_snapshot
        )
    except Exception as e:
        log(f"METRICS ERROR | equity snapshot | {e}")
'''

if old in bot:
    bot = bot.replace(old, new, 1)
else:
    print("WARNING: could not patch NEW CYCLE block")

BOT.write_text(bot)

# add history route to dashboard safely
history_code = r'''

@app.route("/history")
@requires_auth
def history():
    import csv
    import os

    rows = []
    if os.path.exists("equity_history.csv"):
        with open("equity_history.csv", "r") as f:
            rows = list(csv.DictReader(f))[-100:]

    values = []
    labels = []

    for row in rows:
        try:
            values.append(float(row["portfolio_value"]))
            labels.append(row["timestamp"][5:16].replace("T", " "))
        except Exception:
            pass

    points = ""
    if values:
        min_v = min(values)
        max_v = max(values)
        span = max(max_v - min_v, 1)
        width = 900
        height = 260

        coords = []
        for i, value in enumerate(values):
            x = int((i / max(len(values) - 1, 1)) * width)
            y = int(height - ((value - min_v) / span) * height)
            coords.append(f"{x},{y}")

        points = " ".join(coords)

    table_rows = ""
    for row in reversed(rows[-25:]):
        table_rows += f"""
        <tr>
            <td>{row.get('timestamp','')}</td>
            <td>${float(row.get('portfolio_value',0)):,.2f}</td>
            <td>${float(row.get('buying_power',0)):,.2f}</td>
            <td>${float(row.get('open_pl',0)):,.2f}</td>
        </tr>
        """

    if not table_rows:
        table_rows = "<tr><td colspan='4'>No history yet. Let the bot run for a few cycles.</td></tr>"

    return f"""
    <html>
    <head>
        <title>Ponder Invest AI History</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="15">
        <style>
            body {{
                margin:0;
                font-family:Arial;
                background:#030712;
                color:white;
            }}
            .container {{
                max-width:1100px;
                margin:auto;
                padding:24px;
            }}
            .card {{
                background:#0f172a;
                border:1px solid rgba(255,255,255,.1);
                border-radius:22px;
                padding:20px;
                margin-bottom:18px;
            }}
            a {{ color:#00ff88; }}
            table {{
                width:100%;
                border-collapse:collapse;
            }}
            th,td {{
                padding:12px;
                border-bottom:1px solid rgba(255,255,255,.08);
                text-align:left;
            }}
            .muted {{ color:#94a3b8; }}
            svg {{
                width:100%;
                background:#020617;
                border-radius:16px;
                border:1px solid rgba(255,255,255,.08);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ponder Invest AI · History</h1>
            <p><a href="/">← Back to Dashboard</a></p>

            <div class="card">
                <h2>Equity Curve</h2>
                <p class="muted">Tracks portfolio value snapshots collected each bot cycle.</p>
                <svg viewBox="0 0 900 300">
                    <polyline fill="none" stroke="#00ff88" stroke-width="4" points="{points}" transform="translate(0,20)" />
                </svg>
            </div>

            <div class="card">
                <h2>Recent Equity Snapshots</h2>
                <table>
                    <tr>
                        <th>Time</th>
                        <th>Portfolio Value</th>
                        <th>Buying Power</th>
                        <th>Open P/L</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """
'''

if '@app.route("/history")' not in web:
    web = web + history_code

# add dashboard link if exact footer exists
web = web.replace(
    'Ponder Invest AI · Adaptive cloud trading dashboard · <a href="/logout" style="color:#94a3b8;">Logout</a>',
    'Ponder Invest AI · Adaptive cloud trading dashboard · <a href="/history" style="color:#94a3b8;">History</a> · <a href="/logout" style="color:#94a3b8;">Logout</a>'
)

WEB.write_text(web)

print("✅ QOL + safety + history upgrade installed")
print(f"✅ Bot backup: {bot_backup}")
print(f"✅ Dashboard backup: {web_backup}")
print("Now run:")
print("python3 -m py_compile bot.py web_dashboard.py metrics_tracker.py")
print("sudo systemctl restart tradebot")
print("sudo systemctl restart tradebot-dashboard")
print("")
print("Useful commands:")
print("touch STOP_TRADING      # emergency pause")
print("rm STOP_TRADING         # resume")
print("Visit: https://dashboard.ponderinvestai.com/history")
