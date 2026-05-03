from pathlib import Path
from datetime import datetime

WEB = Path("web_dashboard.py")
BOT = Path("bot.py")

web = WEB.read_text()
bot = BOT.read_text()

WEB_BACKUP = Path(f"web_dashboard_backup_mobile_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
BOT_BACKUP = Path(f"bot_backup_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")

WEB_BACKUP.write_text(web)
BOT_BACKUP.write_text(bot)

# =========================
# WEB DASHBOARD: BETTER LOGIN
# =========================
web = web.replace(
    "from flask import Flask, request, Response",
    "from flask import Flask, request, Response, redirect, url_for, session"
)

web = web.replace(
    "import html",
    "import html\nimport secrets"
)

web = web.replace(
    "app = Flask(__name__)",
    'app = Flask(__name__)\napp.secret_key = os.getenv("DASHBOARD_SECRET_KEY", secrets.token_hex(32))'
)

old_auth = '''def requires_auth(func):
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
'''

new_auth = '''def requires_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("logged_in"):
            return func(*args, **kwargs)

        auth = request.authorization
        if auth and check_auth(auth.username, auth.password):
            session["logged_in"] = True
            return func(*args, **kwargs)

        return redirect(url_for("login"))

    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if check_auth(username, password):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))

        error = "Invalid login."

    return f"""
    <html>
    <head>
        <title>Ponder Invest AI Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: radial-gradient(circle at top, rgba(0,255,136,0.18), transparent 35%), #030712;
                color: white;
                display: flex;
                min-height: 100vh;
                align-items: center;
                justify-content: center;
            }}
            .box {{
                width: 92%;
                max-width: 420px;
                background: rgba(15,23,42,0.92);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 24px;
                padding: 28px;
                box-shadow: 0 25px 60px rgba(0,0,0,0.45);
            }}
            h1 {{ margin-top: 0; font-size: 32px; }}
            span {{ color: #00ff88; }}
            input {{
                width: 100%;
                padding: 14px;
                margin: 10px 0;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.12);
                background: #020617;
                color: white;
                font-size: 16px;
            }}
            button {{
                width: 100%;
                padding: 14px;
                border-radius: 14px;
                border: none;
                margin-top: 12px;
                background: #00ff88;
                color: #02120a;
                font-weight: 900;
                font-size: 16px;
            }}
            .error {{ color: #ff5c7a; }}
            .muted {{ color: #94a3b8; }}
        </style>
    </head>
    <body>
        <form class="box" method="POST">
            <h1>Ponder Invest <span>AI</span></h1>
            <p class="muted">Secure dashboard login</p>
            <p class="error">{html.escape(error)}</p>
            <input name="username" placeholder="Username" autocomplete="username">
            <input name="password" placeholder="Password" type="password" autocomplete="current-password">
            <button type="submit">Sign In</button>
        </form>
    </body>
    </html>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
'''

if old_auth in web:
    web = web.replace(old_auth, new_auth)
else:
    print("WARNING: auth block not found")

# Add mobile meta if missing
web = web.replace(
    '<meta http-equiv="refresh" content="5">',
    '<meta http-equiv="refresh" content="5">\\n        <meta name="viewport" content="width=device-width, initial-scale=1">'
)

# Add logout link near footer
web = web.replace(
    "Ponder Invest AI · Adaptive cloud trading dashboard",
    'Ponder Invest AI · Adaptive cloud trading dashboard · <a href="/logout" style="color:#94a3b8;">Logout</a>'
)

# Strong mobile CSS
mobile_css = r'''
            .mobile-bar {
                display: none;
            }

            @media (max-width: 760px) {
                body {
                    font-size: 16px;
                }

                .container {
                    padding: 12px;
                    padding-bottom: 90px;
                }

                .header {
                    position: sticky;
                    top: 0;
                    z-index: 20;
                    background: rgba(3, 7, 18, 0.95);
                    backdrop-filter: blur(14px);
                    padding: 12px;
                    margin: -12px -12px 14px -12px;
                    border-bottom: 1px solid rgba(255,255,255,0.08);
                }

                .brand {
                    font-size: 28px;
                }

                .subtitle {
                    font-size: 13px;
                }

                .grid, .grid-2 {
                    grid-template-columns: 1fr;
                    gap: 12px;
                }

                .card {
                    border-radius: 18px;
                    padding: 16px;
                    margin-bottom: 12px;
                }

                .big {
                    font-size: 26px;
                }

                .status-row {
                    gap: 6px;
                }

                .mini-pill, .pill {
                    font-size: 12px;
                    padding: 7px 10px;
                }

                table {
                    display: block;
                    overflow-x: auto;
                    white-space: nowrap;
                }

                th, td {
                    font-size: 12px;
                    padding: 10px 8px;
                }

                pre {
                    font-size: 12px;
                    max-height: 220px;
                }

                .mobile-bar {
                    display: flex;
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: rgba(3, 7, 18, 0.96);
                    backdrop-filter: blur(14px);
                    border-top: 1px solid rgba(255,255,255,0.1);
                    padding: 10px;
                    gap: 8px;
                    z-index: 30;
                    justify-content: space-around;
                }

                .mobile-bar a {
                    color: white;
                    text-decoration: none;
                    font-size: 12px;
                    background: rgba(255,255,255,0.08);
                    padding: 9px 10px;
                    border-radius: 999px;
                }
            }
'''

web = web.replace("</style>", mobile_css + "\n        </style>", 1)

# Add mobile quick nav before closing body
web = web.replace(
    "</body>",
    '''
        <div class="mobile-bar">
            <a href="#">Top</a>
            <a href="#decisions">Decisions</a>
            <a href="#positions">Positions</a>
            <a href="#logs">Logs</a>
        </div>
    </body>''',
    1
)

# Add anchor ids
web = web.replace("<h3>Live Decision Panel</h3>", '<h3 id="decisions">Live Decision Panel</h3>')
web = web.replace("<h2>Position Ranking</h2>", '<h2 id="positions">Position Ranking</h2>')
web = web.replace("<h2>Recent Bot Logs</h2>", '<h2 id="logs">Recent Bot Logs</h2>')

WEB.write_text(web)

# =========================
# BOT: BETTER ALERTS
# =========================
if "ALERT_CACHE = {}" not in bot:
    bot = bot.replace(
        "last_buy_day = None",
        "last_buy_day = None\n\nALERT_CACHE = {}"
    )

alert_func = r'''
def alert_once(key, message, cooldown_seconds=1800):
    now = time.time()
    last = ALERT_CACHE.get(key, 0)

    if now - last >= cooldown_seconds:
        ALERT_CACHE[key] = now
        notify_discord(message)
'''

if "def alert_once(" not in bot:
    bot = bot.replace(
        "def market_is_open():",
        alert_func + "\n\ndef market_is_open():"
    )

# Alert on enhanced candidates
old_scanner = '    log(f"SCANNER | enhanced candidates={enhanced}")'
new_scanner = '''    log(f"SCANNER | enhanced candidates={enhanced}")
    if enhanced:
        alert_once("scanner_candidates", f"🔎 SCANNER | Enhanced candidates found: {enhanced}", 1800)'''

if old_scanner in bot:
    bot = bot.replace(old_scanner, new_scanner)

# Alert on weak position
old_pl = '        log(f"P/L | {symbol} | {change:.2%}")'
new_pl = '''        log(f"P/L | {symbol} | {change:.2%}")

        if change <= -0.04:
            alert_once(f"weak_position_{symbol}", f"⚠️ WEAK POSITION | {symbol} | P/L {change:.2%}", 3600)'''

if old_pl in bot:
    bot = bot.replace(old_pl, new_pl)

BOT.write_text(bot)

print("✅ Mobile UI, better login, and better alerts injected")
print(f"✅ Web backup: {WEB_BACKUP}")
print(f"✅ Bot backup: {BOT_BACKUP}")
print("Now run:")
print("python3 -m py_compile web_dashboard.py bot.py")
print("sudo systemctl restart tradebot-dashboard")
print("sudo systemctl restart tradebot")
