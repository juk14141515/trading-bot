from pathlib import Path
from datetime import datetime

FILE = Path("web_dashboard.py")

backup = Path(f"web_dashboard_backup_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
text = FILE.read_text()
backup.write_text(text)

start = text.find("    return f\"\"\"")
end = text.find("\n    \"\"\"", start)

if start == -1 or end == -1:
    raise SystemExit("Could not find dashboard HTML block.")

logic_marker = "# === DASHBOARD INTELLIGENCE LOGIC ==="

if logic_marker not in text:
    insert_point = start
    logic = r'''
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
'''
    text = text[:insert_point] + logic + text[insert_point:]

start = text.find("    return f\"\"\"")
end = text.find("\n    \"\"\"", start)

new_html = r'''    return f"""
    <html>
    <head>
        <title>Ponder Invest AI</title>
        <meta http-equiv="refresh" content="10">
        <style>
            * {{ box-sizing: border-box; }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background:
                    radial-gradient(circle at top left, rgba(0,255,136,0.13), transparent 30%),
                    radial-gradient(circle at top right, rgba(59,130,246,0.16), transparent 30%),
                    #050607;
                color: #f8fafc;
            }}

            .container {{
                max-width: 1320px;
                margin: auto;
                padding: 28px;
            }}

            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
            }}

            .brand {{
                font-size: 36px;
                font-weight: 900;
                letter-spacing: -1px;
            }}

            .brand span {{ color: #00ff88; }}

            .subtitle {{
                color: #94a3b8;
                margin-top: 6px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 18px;
                margin-bottom: 18px;
            }}

            .card {{
                background: rgba(15, 23, 42, 0.84);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 22px;
                padding: 22px;
                box-shadow: 0 20px 45px rgba(0,0,0,0.35);
                margin-bottom: 18px;
            }}

            .big {{
                font-size: 30px;
                font-weight: 900;
            }}

            .pill {{
                padding: 10px 16px;
                border-radius: 999px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                font-weight: 800;
            }}

            .green {{ color: #00ff88; }}
            .red {{ color: #ff5c7a; }}
            .yellow {{ color: #ffd84d; }}
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
                padding: 14px 12px;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                text-align: left;
            }}

            tr:hover {{ background: rgba(255,255,255,0.04); }}

            pre {{
                background: #030712;
                padding: 16px;
                border-radius: 16px;
                overflow: auto;
                max-height: 280px;
                color: #d1d5db;
                border: 1px solid rgba(255,255,255,0.08);
            }}

            ul {{ margin: 0; padding-left: 18px; }}
            li {{ margin-bottom: 8px; }}

            .footer {{
                color: #64748b;
                text-align: center;
                padding: 18px;
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <div class="header">
                <div>
                    <div class="brand">Ponder Invest <span>AI</span></div>
                    <div class="subtitle">Autonomous paper-trading system · refreshes every 10 seconds</div>
                </div>
                <div class="pill {status_class}">{bot_status}</div>
            </div>

            <div class="grid">
                <div class="card"><h3>Account Status</h3><div class="big">{account.status}</div><p class="muted">Connected to Alpaca paper trading</p></div>
                <div class="card"><h3>Portfolio Value</h3><div class="big">{money(account.portfolio_value)}</div><p class="muted">Total account value</p></div>
                <div class="card"><h3>Buying Power</h3><div class="big">{money(account.buying_power)}</div><p class="muted">Available deployable capital</p></div>
                <div class="card"><h3>Open P/L</h3><div class="big {'green' if total_pl >= 0 else 'red'}">{money(total_pl)}</div><p class="muted">Unrealized position P/L</p></div>
            </div>

            <div class="grid">
                <div class="card"><h3>Open Win Rate</h3><div class="big">{open_win_rate:.1f}%</div><p class="muted">{open_winners} winners · {open_losers} losers</p></div>
                <div class="card"><h3>Capital Deployed</h3><div class="big">{deployed_pct:.1f}%</div><p class="muted">{money(deployed_value)} currently deployed</p></div>
                <div class="card"><h3>Bot Actions</h3><div class="big">{buy_count + sell_count + skip_count}</div><p class="muted">Buys {buy_count} · Sells {sell_count} · Skips {skip_count}</p></div>
                <div class="card"><h3>Rotations</h3><div class="big">{rotation_count}</div><p class="muted">Approved rotation events in recent logs</p></div>
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
                    <h3>Live Decision Panel</h3>
                    <ul>{decision_items}</ul>
                </div>

                <div class="card">
                    <h3>AI Reasoning Feed</h3>
                    <ul>{ai_feed_items}</ul>
                </div>
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
                Ponder Invest AI · Cloud trading dashboard
            </div>

        </div>
    </body>
    </html>
    """'''

updated = text[:start] + new_html + text[end + len('\n    """'):]
FILE.write_text(updated)

print("✅ Intelligence dashboard injected")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
