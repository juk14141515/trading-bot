from flask import Flask
import alpaca_trade_api as tradeapi

API_KEY = "PK54UWSJEP5SMKSMLZMI4AQMLS"
SECRET_KEY = "6quBqLTFABUB5pbhjgaS4TsCdq8iUmXQWSXrNjRdofzp"
BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

app = Flask(__name__)

def read_logs():
    try:
        with open("log.txt", "r") as f:
            return f.readlines()[-30:]
    except FileNotFoundError:
        return ["No log file found yet."]

@app.route("/")
def dashboard():
    account = api.get_account()
    positions = api.list_positions()
    clock = api.get_clock()
    logs = read_logs()

    html = """
    <html>
    <head>
        <title>Trading Bot Dashboard</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial; background: #111; color: white; padding: 25px; }
            .card { background: #1e1e1e; padding: 20px; margin: 15px 0; border-radius: 10px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; border-bottom: 1px solid #444; }
            .green { color: #00ff88; }
            .red { color: #ff5555; }
            pre { white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>Trading Bot Dashboard</h1>

        <div class="card">
            <h2>Account</h2>
            <p>Status: {status}</p>
            <p>Market Open: {market_open}</p>
            <p>Equity: ${equity}</p>
            <p>Buying Power: ${buying_power}</p>
            <p>Portfolio Value: ${portfolio_value}</p>
        </div>

        <div class="card">
            <h2>Open Positions</h2>
            <table>
                <tr>
                    <th>Symbol</th>
                    <th>Qty</th>
                    <th>Entry</th>
                    <th>Current</th>
                    <th>P/L %</th>
                </tr>
                {positions}
            </table>
        </div>

        <div class="card">
            <h2>Recent Logs</h2>
            <pre>{logs}</pre>
        </div>
    </body>
    </html>
    """

    position_rows = ""

    for p in positions:
        plpc = float(p.unrealized_plpc) * 100
        color = "green" if plpc >= 0 else "red"

        position_rows += f"""
        <tr>
            <td>{p.symbol}</td>
            <td>{p.qty}</td>
            <td>${p.avg_entry_price}</td>
            <td>${p.current_price}</td>
            <td class="{color}">{plpc:.2f}%</td>
        </tr>
        """

    if not position_rows:
        position_rows = "<tr><td colspan='5'>No open positions</td></tr>"

    return html.replace("{status}", str(account.status)) \
        .replace("{market_open}", str(clock.is_open)) \
        .replace("{equity}", str(account.equity)) \
        .replace("{buying_power}", str(account.buying_power)) \
        .replace("{portfolio_value}", str(account.portfolio_value)) \
        .replace("{positions}", position_rows) \
        .replace("{logs}", "".join(logs))

if __name__ == "__main__":
    app.run(debug=True)