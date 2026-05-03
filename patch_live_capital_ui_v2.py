from pathlib import Path

CAP = Path("capital_intelligence_v1.py")
DASH = Path("new_ponder_site/templates/dashboard.html")

CAP.with_suffix(".py.backup_live_v2").write_text(CAP.read_text())
DASH.with_suffix(".html.backup_live_v2").write_text(DASH.read_text())

cap = CAP.read_text()

cap = cap.replace(
'from dotenv import load_dotenv\nimport os',
'from dotenv import load_dotenv\nimport os'
)

cap = cap.replace(
'load_dotenv()',
'env_path = Path(__file__).resolve().parent / ".env"\nload_dotenv(dotenv_path=env_path)'
)

CAP.write_text(cap)

dash = DASH.read_text()

dash = dash.replace(
'document.getElementById("m-equity").textContent = fmtMoney(c.equity);',
'document.getElementById("m-equity").textContent = fmtMoney(c.portfolio_value || c.equity);'
)

dash = dash.replace(
'ctx.strokeStyle = "rgba(167,139,250,.95)";',
'''ctx.strokeStyle = nums[nums.length-1] >= nums[0]
    ? "rgba(142,233,154,.9)"
    : "rgba(255,107,122,.9)";'''
)

dash = dash.replace(
'''document.getElementById("m-today").textContent = fmtMoney(c.today_pl);''',
'''const todayEl = document.getElementById("m-today");
  todayEl.textContent = fmtMoney(c.today_pl);
  todayEl.style.color = c.today_pl > 0 ? "#8ee99a" : c.today_pl < 0 ? "#ff6b7a" : "#eef2ff";'''
)

dash = dash.replace(
'''document.getElementById("m-week").textContent = fmtMoney(c.week_pl);''',
'''const weekEl = document.getElementById("m-week");
  weekEl.textContent = fmtMoney(c.week_pl);
  weekEl.style.color = c.week_pl > 0 ? "#8ee99a" : c.week_pl < 0 ? "#ff6b7a" : "#eef2ff";'''
)

dash = dash.replace(
'''document.getElementById("m-all").textContent = fmtMoney(c.all_time_pl);''',
'''const allEl = document.getElementById("m-all");
  allEl.textContent = fmtMoney(c.all_time_pl);
  allEl.style.color = c.all_time_pl > 0 ? "#8ee99a" : c.all_time_pl < 0 ? "#ff6b7a" : "#eef2ff";'''
)

dash = dash.replace(
'''document.getElementById("money-next").textContent = c.next_money_action || "";''',
'''document.getElementById("money-next").textContent = c.next_money_action || "";

  const pulse = document.getElementById("m-equity");
  if (pulse) {
    pulse.style.transition = "all 0.25s ease";
    pulse.style.transform = "scale(1.04)";
    setTimeout(() => pulse.style.transform = "scale(1)", 180);
  }'''
)

dash = dash.replace("30000", "5000")

DASH.write_text(dash)

print("✅ Patched live capital UI v2")
print("Backups created.")
