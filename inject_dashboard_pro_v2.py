from pathlib import Path
from datetime import datetime

FILE = Path("web_dashboard.py")

if not FILE.exists():
    raise SystemExit("web_dashboard.py not found")

text = FILE.read_text()
backup = Path(f"web_dashboard_backup_pro_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(text)

start = text.find("    return f\"\"\"")
end = text.find("\n    \"\"\"", start)

if start == -1 or end == -1:
    raise SystemExit("Could not find dashboard HTML block")

logic_marker = "# === PRO DASHBOARD LOGIC V2 ==="

if logic_marker not in text:
    logic = r'''
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
'''
    text = text[:start] + logic + text[start:]

start = text.find("    return f\"\"\"")
end = text.find("\n    \"\"\"", start)

new_html = r'''    return f"""
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
    """'''

updated = text[:start] + new_html + text[end + len('\n    """'):]
FILE.write_text(updated)

print("✅ Pro dashboard v2 injected")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
