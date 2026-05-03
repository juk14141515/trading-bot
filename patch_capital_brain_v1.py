from pathlib import Path

CAP = Path("capital_intelligence_v1.py")
DASH = Path("new_ponder_site/templates/dashboard.html")

CAP.with_suffix(".py.backup_capital_brain_v1").write_text(CAP.read_text())
DASH.with_suffix(".html.backup_capital_brain_v1").write_text(DASH.read_text())

cap = CAP.read_text()

cap = cap.replace(
    'open_pl = round(equity - portfolio_value, 2)',
    'open_pl = safe_float(getattr(acct, "unrealized_pl", 0))'
)

cap = cap.replace(
'''if used_pct < 35:
            mode = "UNDERUTILIZED"
            action = "Capital is mostly idle. Only deploy if Decision Feed improves."
        elif used_pct < 75:
            mode = "BALANCED"
            action = "Capital usage is reasonable. Focus on quality over quantity."
        else:
            mode = "HEAVY"
            action = "Capital is heavily used. Prioritize exits, rotation, and risk control."''',
'''if used_pct < 35:
            mode = "UNDERUTILIZED"
        elif used_pct < 75:
            mode = "BALANCED"
        else:
            mode = "HEAVY"

        if used_pct < 30:
            efficiency = "LOW"
        elif used_pct < 70:
            efficiency = "GOOD"
        else:
            efficiency = "HIGH"

        if deployable_cash > 50000 and today_pl <= 0:
            action = "WAIT — No edge detected. Protect capital."
        elif deployable_cash > 50000:
            action = "READY — Capital available for strong setups."
        elif used_pct > 70:
            action = "MANAGE — Focus on current positions."
        else:
            action = "BUILD — Slowly deploy into best setups."'''
)

cap = cap.replace(
'''            "capital_mode": mode,
            "next_money_action": action,''',
'''            "capital_mode": mode,
            "capital_efficiency": efficiency,
            "next_money_action": action,'''
)

cap = cap.replace(
'''            "equity": round(equity, 2),''',
'''            "equity": round(portfolio_value, 2),'''
)

CAP.write_text(cap)

dash = DASH.read_text()

dash = dash.replace(
'''<div><strong>Portfolio</strong><span id="m-equity">${{ "{:,.2f}".format(capital.get("equity", 0)|float) }}</span></div>
    <div><strong>Today P/L</strong><span id="m-today">${{ "{:,.2f}".format(capital.get("today_pl", 0)|float) }}</span></div>''',
'''<div><strong>Today P/L</strong><span id="m-today">${{ "{:,.2f}".format(capital.get("today_pl", 0)|float) }}</span></div>
    <div><strong>Portfolio</strong><span id="m-equity">${{ "{:,.2f}".format(capital.get("equity", 0)|float) }}</span></div>'''
)

dash = dash.replace(
'''<div><strong>Deployable</strong><span id="m-deploy">${{ "{:,.2f}".format(capital.get("deployable_cash", 0)|float) }}</span></div>''',
'''<div><strong>Deployable</strong><span id="m-deploy">${{ "{:,.2f}".format(capital.get("deployable_cash", 0)|float) }}</span></div>
    <div><strong>Efficiency</strong><span id="m-eff">{{ capital.get("capital_efficiency", "—") }}</span></div>'''
)

dash = dash.replace(
'''document.getElementById("m-deploy").textContent = fmtMoney(c.deployable_cash);''',
'''document.getElementById("m-deploy").textContent = fmtMoney(c.deployable_cash);
  const eff = document.getElementById("m-eff");
  if (eff) eff.textContent = c.capital_efficiency || "—";'''
)

DASH.write_text(dash)

print("✅ Capital brain patch installed.")
print("Backups created.")
