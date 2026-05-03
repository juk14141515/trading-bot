from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
APP = ROOT / "new_ponder_site/app.py"
PIPE = ROOT / "research_pipeline_v1.py"
DASH = ROOT / "new_ponder_site/templates/dashboard.html"
CSS = ROOT / "new_ponder_site/static/style.css"

for p in [APP, PIPE, DASH, CSS]:
    p.with_suffix(p.suffix + ".backup_capital_v1").write_text(p.read_text())

# Create read-only capital intelligence
(ROOT / "capital_intelligence_v1.py").write_text(r'''import os, json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)
DEST = OUT / "capital_intelligence_latest.json"

RESERVE_PCT = float(os.getenv("PONDER_RESERVE_PCT", "20"))

def safe_float(x, default=0):
    try:
        return float(x)
    except Exception:
        return default

def main():
    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "research_only",
        "source": "alpaca_read_only",
        "reserve_pct": RESERVE_PCT,
        "equity": 0,
        "cash": 0,
        "buying_power": 0,
        "portfolio_value": 0,
        "reserve_cash": 0,
        "deployable_cash": 0,
        "capital_used_pct": 0,
        "capital_mode": "UNKNOWN",
        "next_money_action": "No account data yet.",
        "notes": [
            "Read-only capital intelligence.",
            "Does not place trades.",
            "Used for dashboard planning and future allocator research."
        ]
    }

    try:
        import alpaca_trade_api as tradeapi

        key = os.getenv("APCA_API_KEY_ID")
        secret = os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

        if not key or not secret:
            raise RuntimeError("Missing Alpaca env keys")

        api = tradeapi.REST(key, secret, base_url, api_version="v2")
        acct = api.get_account()

        equity = safe_float(acct.equity)
        cash = safe_float(acct.cash)
        buying_power = safe_float(acct.buying_power)
        portfolio_value = safe_float(acct.portfolio_value)

        reserve_cash = round(equity * (RESERVE_PCT / 100), 2)
        deployable_cash = round(max(0, cash - reserve_cash), 2)
        used_pct = round(max(0, min(100, (1 - (cash / equity)) * 100 if equity else 0)), 2)

        if used_pct < 35:
            mode = "UNDERUTILIZED"
            action = "Capital is mostly idle. Only deploy if Decision Feed improves."
        elif used_pct < 75:
            mode = "BALANCED"
            action = "Capital usage is reasonable. Focus on quality over quantity."
        else:
            mode = "HEAVY"
            action = "Capital is heavily used. Prioritize exits, rotation, and risk control."

        payload.update({
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "buying_power": round(buying_power, 2),
            "portfolio_value": round(portfolio_value, 2),
            "reserve_cash": reserve_cash,
            "deployable_cash": deployable_cash,
            "capital_used_pct": used_pct,
            "capital_mode": mode,
            "next_money_action": action
        })

    except Exception as e:
        payload["error"] = str(e)

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps({
        "capital_mode": payload["capital_mode"],
        "cash": payload["cash"],
        "buying_power": payload["buying_power"],
        "deployable_cash": payload["deployable_cash"]
    }, indent=2))

if __name__ == "__main__":
    main()
''')

# Patch pipeline
pipe = PIPE.read_text()
if 'run(["python3", "capital_intelligence_v1.py"])' not in pipe:
    pipe = pipe.replace(
        'run(["python3", "decision_research_v1.py"])',
        'run(["python3", "decision_research_v1.py"])\n    run(["python3", "capital_intelligence_v1.py"])'
    )
PIPE.write_text(pipe)

# Patch app
app = APP.read_text()
if '"capital": load_json("capital_intelligence_latest.json")' not in app:
    app = app.replace(
        '"decisions": load_json("decision_engine_latest.json"),',
        '"decisions": load_json("decision_engine_latest.json"),\n        "capital": load_json("capital_intelligence_latest.json"),'
    )
APP.write_text(app)

dash = DASH.read_text()

if '{% set capital = data.get("capital", {}) %}' not in dash:
    dash = dash.replace(
        '{% set decisions = data.get("decisions", {}) %}',
        '{% set decisions = data.get("decisions", {}) %}\n{% set capital = data.get("capital", {}) %}'
    )

capital_panel = r'''
<section class="card capital-command">
  <div>
    <div class="eyebrow">Capital Command</div>
    <h2>💰 Cash + Buying Power</h2>
    <p class="muted">{{ capital.get("next_money_action", "Run capital intelligence to load account data.") }}</p>
  </div>

  <div class="capital-grid">
    <div><strong>Cash</strong><span>${{ "{:,.2f}".format(capital.get("cash", 0)|float) }}</span></div>
    <div><strong>Buying Power</strong><span>${{ "{:,.2f}".format(capital.get("buying_power", 0)|float) }}</span></div>
    <div><strong>Reserve</strong><span>${{ "{:,.2f}".format(capital.get("reserve_cash", 0)|float) }}</span></div>
    <div><strong>Deployable</strong><span>${{ "{:,.2f}".format(capital.get("deployable_cash", 0)|float) }}</span></div>
  </div>

  <div class="strength-wrap">
    <span>Capital Used</span>
    <div class="strength-track">
      <div class="strength-fill" style="width: {{ capital.get("capital_used_pct", 0) }}%"></div>
    </div>
    <strong>{{ capital.get("capital_used_pct", "—") }}%</strong>
  </div>

  <div class="capital-note">
    Mode: <strong>{{ capital.get("capital_mode", "UNKNOWN") }}</strong> · Reserve target: {{ capital.get("reserve_pct", 20) }}%
  </div>
</section>
'''

if "Capital Command" not in dash:
    dash = dash.replace('<section class="split">', capital_panel + '\n\n<section class="split">')

DASH.write_text(dash)

css = CSS.read_text()
if "Capital Command v1" not in css:
    css += r'''

/* ===== Capital Command v1 ===== */
.capital-command {
  border-color:rgba(167,139,250,.45);
  background:
    radial-gradient(circle at top right, rgba(167,139,250,.14), transparent 35%),
    linear-gradient(180deg,var(--card),#090d15);
}

.capital-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
  margin:18px 0;
}

.capital-grid div {
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  background:rgba(255,255,255,.025);
}

.capital-grid strong {
  display:block;
  color:var(--muted);
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:.08em;
  margin-bottom:8px;
}

.capital-grid span {
  font-size:20px;
  font-weight:900;
}

.capital-note {
  margin-top:14px;
  color:var(--muted);
}

@media (max-width:850px) {
  .capital-grid {
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}
'''
CSS.write_text(css)

print("✅ Installed Capital Intelligence + dashboard capital command panel.")
