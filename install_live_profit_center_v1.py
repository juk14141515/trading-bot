from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
CAP = ROOT / "capital_intelligence_v1.py"
APP = ROOT / "new_ponder_site/app.py"
DASH = ROOT / "new_ponder_site/templates/dashboard.html"
CSS = ROOT / "new_ponder_site/static/style.css"

for p in [CAP, APP, DASH, CSS]:
    p.with_suffix(p.suffix + ".backup_profit_center_v1").write_text(p.read_text())

CAP.write_text(r'''import os, json, csv
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)
DEST = OUT / "capital_intelligence_latest.json"
HISTORY = OUT / "capital_history.csv"

RESERVE_PCT = float(os.getenv("PONDER_RESERVE_PCT", "20"))

def safe_float(x, default=0):
    try:
        return float(x)
    except Exception:
        return default

def read_history():
    if not HISTORY.exists():
        return []
    with HISTORY.open() as f:
        return list(csv.DictReader(f))

def write_history(row):
    exists = HISTORY.exists()
    with HISTORY.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "equity", "cash", "buying_power", "portfolio_value", "open_pl"
        ])
        if not exists:
            writer.writeheader()
        writer.writerow(row)

def nearest_baseline(rows, target_dt):
    if not rows:
        return None
    best = None
    best_gap = None
    for r in rows:
        try:
            t = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
            gap = abs((t - target_dt).total_seconds())
            if best is None or gap < best_gap:
                best = r
                best_gap = gap
        except Exception:
            pass
    return best

def pnl_from_baseline(current, base):
    if not base:
        return 0
    return round(current - safe_float(base.get("equity")), 2)

def main():
    now_dt = datetime.now()
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "updated_at": now,
        "status": "research_only",
        "source": "alpaca_read_only",
        "reserve_pct": RESERVE_PCT,
        "equity": 0,
        "cash": 0,
        "buying_power": 0,
        "portfolio_value": 0,
        "open_pl": 0,
        "today_pl": 0,
        "week_pl": 0,
        "all_time_pl": 0,
        "reserve_cash": 0,
        "deployable_cash": 0,
        "capital_used_pct": 0,
        "capital_mode": "UNKNOWN",
        "next_money_action": "No account data yet.",
        "history": [],
        "notes": [
            "Read-only live profit and capital intelligence.",
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
        open_pl = round(equity - portfolio_value, 2)

        row = {
            "timestamp": now,
            "equity": round(equity, 2),
            "cash": round(cash, 2),
            "buying_power": round(buying_power, 2),
            "portfolio_value": round(portfolio_value, 2),
            "open_pl": round(open_pl, 2),
        }
        write_history(row)

        rows = read_history()
        first = rows[0] if rows else None
        day_base = nearest_baseline(rows, now_dt.replace(hour=0, minute=0, second=0, microsecond=0))
        week_base = nearest_baseline(rows, now_dt - timedelta(days=7))

        today_pl = pnl_from_baseline(equity, day_base)
        week_pl = pnl_from_baseline(equity, week_base)
        all_time_pl = pnl_from_baseline(equity, first)

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
            "open_pl": round(open_pl, 2),
            "today_pl": today_pl,
            "week_pl": week_pl,
            "all_time_pl": all_time_pl,
            "reserve_cash": reserve_cash,
            "deployable_cash": deployable_cash,
            "capital_used_pct": used_pct,
            "capital_mode": mode,
            "next_money_action": action,
            "history": rows[-120:]
        })

    except Exception as e:
        payload["error"] = str(e)

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)

if __name__ == "__main__":
    main()
''')

# Ensure dashboard loads capital
app = APP.read_text()
if '"capital": load_json("capital_intelligence_latest.json")' not in app:
    app = app.replace(
        '"decisions": load_json("decision_engine_latest.json"),',
        '"decisions": load_json("decision_engine_latest.json"),\n        "capital": load_json("capital_intelligence_latest.json"),'
    )

# Add API route if missing
if '@app.route("/api/dashboard")' not in app:
    app = app.replace(
'''@app.route("/health")
def health():''',
'''@app.route("/api/dashboard")
@auth_required
def api_dashboard():
    return jsonify(dashboard_data())


@app.route("/health")
def health():'''
    )

APP.write_text(app)

dash = DASH.read_text()

if '{% set capital = data.get("capital", {}) %}' not in dash:
    dash = dash.replace(
        '{% set decisions = data.get("decisions", {}) %}',
        '{% set decisions = data.get("decisions", {}) %}\n{% set capital = data.get("capital", {}) %}'
    )

money_panel = r'''
<section class="card money-center">
  <div class="money-head">
    <div>
      <div class="eyebrow">Live Money Center</div>
      <h2>💵 Portfolio + Profit</h2>
      <p class="muted">Read-only Alpaca data. Updates when capital intelligence runs.</p>
    </div>
    <div class="mode-badge mode-selective">{{ capital.get("capital_mode", "UNKNOWN") }}</div>
  </div>

  <div class="money-grid">
    <div><strong>Portfolio</strong><span id="m-equity">${{ "{:,.2f}".format(capital.get("equity", 0)|float) }}</span></div>
    <div><strong>Today P/L</strong><span id="m-today">${{ "{:,.2f}".format(capital.get("today_pl", 0)|float) }}</span></div>
    <div><strong>7-Day P/L</strong><span id="m-week">${{ "{:,.2f}".format(capital.get("week_pl", 0)|float) }}</span></div>
    <div><strong>All-Time P/L</strong><span id="m-all">${{ "{:,.2f}".format(capital.get("all_time_pl", 0)|float) }}</span></div>
    <div><strong>Buying Power</strong><span id="m-bp">${{ "{:,.2f}".format(capital.get("buying_power", 0)|float) }}</span></div>
    <div><strong>Deployable</strong><span id="m-deploy">${{ "{:,.2f}".format(capital.get("deployable_cash", 0)|float) }}</span></div>
  </div>

  <div class="money-charts">
    <div>
      <h3>Equity Curve</h3>
      <canvas id="moneyEquityChart" height="160"></canvas>
    </div>
    <div>
      <h3>P/L Snapshot</h3>
      <canvas id="moneyPlChart" height="160"></canvas>
    </div>
  </div>

  <p class="muted" id="money-next">{{ capital.get("next_money_action", "Run capital intelligence to load account data.") }}</p>
</section>
'''

if "Live Money Center" not in dash:
    dash = dash.replace('<section class="card brainline">', money_panel + '\n\n<section class="card brainline">')

# Add JS chart functions before endblock
extra_js = r'''
<script>
function fmtMoney(n) {
  n = Number(n || 0);
  return "$" + n.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
}

function drawMoneyLine(canvasId, rows, key) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.offsetWidth;
  const h = canvas.height;
  ctx.clearRect(0,0,w,h);

  const nums = (rows || []).map(r => Number(r[key] || 0)).filter(n => !isNaN(n));
  if (nums.length < 2) {
    ctx.fillStyle = "#a7afc3";
    ctx.font = "14px system-ui";
    ctx.fillText("Collecting history...", 12, 40);
    return;
  }

  const min = Math.min(...nums), max = Math.max(...nums);
  const range = Math.max(max - min, 1);

  ctx.strokeStyle = "rgba(167,139,250,.95)";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  nums.forEach((v,i) => {
    const x = 10 + (i/(nums.length-1))*(w-20);
    const y = h-20-((v-min)/range)*(h-42);
    if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.stroke();

  ctx.fillStyle = "#a7afc3";
  ctx.font = "12px system-ui";
  ctx.fillText(fmtMoney(nums[nums.length-1]), 12, 18);
}

function drawMoneyBars(canvasId, values, labels) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.offsetWidth;
  const h = canvas.height;
  ctx.clearRect(0,0,w,h);

  const max = Math.max(...values.map(v => Math.abs(v)), 1);
  const zeroY = h / 2;
  const gap = 16;
  const barW = (w - gap*(values.length+1))/values.length;

  ctx.strokeStyle = "rgba(255,255,255,.12)";
  ctx.beginPath();
  ctx.moveTo(0, zeroY);
  ctx.lineTo(w, zeroY);
  ctx.stroke();

  values.forEach((v,i) => {
    const x = gap + i*(barW+gap);
    const bh = (Math.abs(v)/max)*(h/2-28);
    const y = v >= 0 ? zeroY - bh : zeroY;
    ctx.fillStyle = v >= 0 ? "rgba(142,233,154,.75)" : "rgba(255,107,122,.75)";
    ctx.fillRect(x,y,barW,bh);
    ctx.fillStyle = "#a7afc3";
    ctx.font = "12px system-ui";
    ctx.fillText(labels[i], x, h-6);
  });
}

function renderMoney(data) {
  const c = data.capital || {};
  document.getElementById("m-equity").textContent = fmtMoney(c.equity);
  document.getElementById("m-today").textContent = fmtMoney(c.today_pl);
  document.getElementById("m-week").textContent = fmtMoney(c.week_pl);
  document.getElementById("m-all").textContent = fmtMoney(c.all_time_pl);
  document.getElementById("m-bp").textContent = fmtMoney(c.buying_power);
  document.getElementById("m-deploy").textContent = fmtMoney(c.deployable_cash);
  document.getElementById("money-next").textContent = c.next_money_action || "";

  drawMoneyLine("moneyEquityChart", c.history || [], "equity");
  drawMoneyBars("moneyPlChart", [c.today_pl || 0, c.week_pl || 0, c.all_time_pl || 0], ["Day", "Week", "All"]);
}

renderMoney({{ data | tojson }});
setInterval(async () => {
  try {
    const r = await fetch("/api/dashboard", {cache:"no-store"});
    if (!r.ok) return;
    renderMoney(await r.json());
  } catch(e) {}
}, 30000);
</script>
'''

if "renderMoney" not in dash:
    dash = dash.replace("{% endblock %}", extra_js + "\n{% endblock %}")

DASH.write_text(dash)

css = CSS.read_text()
if "Live Money Center v1" not in css:
    css += r'''

/* ===== Live Money Center v1 ===== */
.money-center {
  border-color:rgba(142,233,154,.35);
  background:
    radial-gradient(circle at top left, rgba(142,233,154,.12), transparent 34%),
    linear-gradient(180deg,var(--card),#090d15);
}

.money-head {
  display:flex;
  justify-content:space-between;
  gap:16px;
  align-items:center;
  margin-bottom:18px;
}

.money-grid {
  display:grid;
  grid-template-columns:repeat(6,minmax(0,1fr));
  gap:12px;
}

.money-grid div {
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  background:rgba(255,255,255,.025);
}

.money-grid strong {
  display:block;
  color:var(--muted);
  text-transform:uppercase;
  letter-spacing:.08em;
  font-size:12px;
  margin-bottom:8px;
}

.money-grid span {
  font-size:22px;
  font-weight:900;
}

.money-charts {
  display:grid;
  grid-template-columns:1.5fr 1fr;
  gap:14px;
  margin-top:18px;
}

.money-charts canvas {
  width:100%;
  border:1px solid var(--line);
  border-radius:16px;
  background:rgba(255,255,255,.018);
}

@media (max-width:1200px) {
  .money-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
  .money-charts { grid-template-columns:1fr; }
}

@media (max-width:700px) {
  .money-head { display:block; }
  .money-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
'''
CSS.write_text(css)

print("✅ Installed live profit center.")
