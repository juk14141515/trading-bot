from pathlib import Path
from datetime import datetime

FILE = Path("web_dashboard.py")

if not FILE.exists():
    raise SystemExit("web_dashboard.py not found")

backup = Path(f"web_dashboard_backup_clean_ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
original = FILE.read_text()
backup.write_text(original)

start = original.find("    return f\"\"\"")
if start == -1:
    raise SystemExit("Could not find dashboard HTML start")

end = original.find("\n    \"\"\"", start)
if end == -1:
    raise SystemExit("Could not find dashboard HTML end")

# Add ranking logic before HTML return if missing
ranking_marker = "# === POSITION RANKING UI LOGIC ==="
if ranking_marker not in original:
    logic_insert_point = original.find("    return f\"\"\"", 0)
    ranking_logic = f'''
    {ranking_marker}
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
            <td>{{html.escape(p.symbol)}} {{flag}}</td>
            <td>{{p.qty}}</td>
            <td>{{money(p.avg_entry_price)}}</td>
            <td>{{money(p.current_price)}}</td>
            <td class="{{color}}">{{money(pl)}}</td>
            <td class="{{color}}">{{float(p.unrealized_plpc) * 100:.2f}}%</td>
            <td>{{round(score, 1)}}</td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='7'>No open positions</td></tr>"

'''
    original = original[:logic_insert_point] + ranking_logic + original[logic_insert_point:]

# Recalculate after insertion
start = original.find("    return f\"\"\"")
end = original.find("\n    \"\"\"", start)

new_html = r'''    return f"""
    <html>
    <head>
        <title>Ponder Invest AI</title>
        <meta http-equiv="refresh" content="10">
        <style>
            * {{
                box-sizing: border-box;
            }}

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
                max-width: 1280px;
                margin: auto;
                padding: 28px;
            }}

            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 20px;
                margin-bottom: 24px;
            }}

            .brand {{
                font-size: 36px;
                font-weight: 900;
                letter-spacing: -1px;
            }}

            .brand span {{
                color: #00ff88;
            }}

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
                background: rgba(15, 23, 42, 0.82);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 22px;
                padding: 22px;
                box-shadow: 0 20px 45px rgba(0,0,0,0.35);
                margin-bottom: 18px;
            }}

            .card h2, .card h3 {{
                margin-top: 0;
            }}

            .big {{
                font-size: 30px;
                font-weight: 900;
            }}

            .pill {{
                display: inline-block;
                padding: 10px 16px;
                border-radius: 999px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                font-weight: 800;
            }}

            .green {{ color: #00ff88; }}
            .red {{ color: #ff5c7a; }}
            .yellow {{ color: #ffd84d; }}

            .muted {{
                color: #94a3b8;
            }}

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

            tr:hover {{
                background: rgba(255,255,255,0.04);
            }}

            pre {{
                background: #030712;
                padding: 16px;
                border-radius: 16px;
                overflow: auto;
                max-height: 280px;
                color: #d1d5db;
                border: 1px solid rgba(255,255,255,0.08);
            }}

            ul {{
                margin: 0;
                padding-left: 18px;
            }}

            li {{
                margin-bottom: 8px;
            }}

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
                    <p class="muted">Unrealized position profit/loss</p>
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

updated = original[:start] + new_html + original[end + len('\n    """'):]

FILE.write_text(updated)

print("✅ Clean Ponder Invest AI dashboard injected")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
