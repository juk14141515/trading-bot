from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_rotation_confidence_v2_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

old = '''def build_rotation_suggestions(positions):
    suggestions = []
    if not positions:
        return [{
            "action": "WAIT",
            "symbol": "-",
            "reason": "No open positions to rotate.",
            "severity": "info"
        }]

    ranked = sorted(
        positions,
        key=lambda p: (
            float(p.get("unrealized_plpc", 0)),
            float(p.get("unrealized_pl", 0))
        )
    )

    weakest = ranked[0]
    pnl_pct = float(weakest.get("unrealized_plpc", 0))
    pnl = float(weakest.get("unrealized_pl", 0))
    symbol = weakest.get("symbol", "-")

    if pnl_pct <= -4:
        suggestions.append({
            "action": "WATCH CLOSELY",
            "symbol": symbol,
            "reason": f"Weakest position is down {pnl_pct:.2f}% / ${pnl:.2f}. Candidate for future rotation or guard review.",
            "severity": "bad"
        })
    elif pnl_pct <= -2:
        suggestions.append({
            "action": "MONITOR",
            "symbol": symbol,
            "reason": f"Position is meaningfully negative at {pnl_pct:.2f}%. Do not rotate automatically yet; collect more closed-trade data.",
            "severity": "warn"
        })
    else:
        suggestions.append({
            "action": "HOLD",
            "symbol": symbol,
            "reason": f"Weakest position is only {pnl_pct:.2f}%. No rotation pressure right now.",
            "severity": "good"
        })

    winners = [p for p in positions if float(p.get("unrealized_pl", 0)) > 0]
    losers = [p for p in positions if float(p.get("unrealized_pl", 0)) < 0]

    suggestions.append({
        "action": "POSITION MIX",
        "symbol": "ALL",
        "reason": f"{len(winners)} winners / {len(losers)} losers. Rotation should stay suggestion-only until 15–20 closed trades.",
        "severity": "info"
    })

    return suggestions
'''

new = '''def build_rotation_suggestions(positions):
    suggestions = []
    if not positions:
        return [{
            "action": "WAIT",
            "symbol": "-",
            "confidence": 0,
            "simulated_improvement": 0,
            "reason": "No open positions to rotate.",
            "severity": "info"
        }]

    ranked = sorted(
        positions,
        key=lambda p: (
            float(p.get("unrealized_plpc", 0)),
            float(p.get("unrealized_pl", 0))
        )
    )

    weakest = ranked[0]
    strongest = ranked[-1]

    pnl_pct = float(weakest.get("unrealized_plpc", 0))
    pnl = float(weakest.get("unrealized_pl", 0))
    mv = float(weakest.get("market_value", 0))
    symbol = weakest.get("symbol", "-")

    total_value = sum(float(p.get("market_value", 0)) for p in positions)
    losing_value = sum(float(p.get("market_value", 0)) for p in positions if float(p.get("unrealized_pl", 0)) < 0)
    exposure_ratio = (losing_value / total_value) if total_value else 0

    severity_points = min(45, max(0, abs(pnl_pct) * 8))
    exposure_points = min(25, exposure_ratio * 25)
    drag_points = min(20, max(0, abs(pnl) / 50))
    confidence = int(min(95, severity_points + exposure_points + drag_points))

    # Simulation is intentionally conservative and display-only.
    # It estimates avoided drag, not guaranteed profit.
    simulated_improvement = 0
    if pnl < 0:
        simulated_improvement = round(min(abs(pnl), mv * 0.015), 2)

    if pnl_pct <= -4:
        action = "WATCH CLOSELY"
        severity = "bad"
        reason = (
            f"Weakest position is down {pnl_pct:.2f}% / ${pnl:.2f}. "
            f"Rotation pressure is elevated, but this remains suggestion-only."
        )
    elif pnl_pct <= -2:
        action = "MONITOR"
        severity = "warn"
        reason = (
            f"Position is meaningfully negative at {pnl_pct:.2f}%. "
            f"Do not auto-rotate yet; keep collecting closed-trade data."
        )
    else:
        action = "HOLD"
        severity = "good"
        reason = f"Weakest position is only {pnl_pct:.2f}%. No rotation pressure right now."

    suggestions.append({
        "action": action,
        "symbol": symbol,
        "confidence": confidence,
        "simulated_improvement": simulated_improvement,
        "reason": reason,
        "severity": severity
    })

    winners = [p for p in positions if float(p.get("unrealized_pl", 0)) > 0]
    losers = [p for p in positions if float(p.get("unrealized_pl", 0)) < 0]

    suggestions.append({
        "action": "POSITION MIX",
        "symbol": "ALL",
        "confidence": int(exposure_ratio * 100),
        "simulated_improvement": 0,
        "reason": f"{len(winners)} winners / {len(losers)} losers. Rotation should stay suggestion-only until 15–20 closed trades.",
        "severity": "info"
    })

    if strongest and strongest.get("symbol") != symbol:
        suggestions.append({
            "action": "BEST OFFSET",
            "symbol": strongest.get("symbol", "-"),
            "confidence": 0,
            "simulated_improvement": 0,
            "reason": (
                f"Best open offset is {strongest.get('symbol', '-')} "
                f"at {float(strongest.get('unrealized_plpc', 0)):.2f}% / "
                f"${float(strongest.get('unrealized_pl', 0)):.2f}."
            ),
            "severity": "good"
        })

    return suggestions
'''

if old in txt:
    txt = txt.replace(old, new)
else:
    print("WARNING: exact build_rotation_suggestions block not found. Skipping backend replace.")

# Upgrade table headers
txt = txt.replace(
    '<thead><tr><th>Action</th><th>Symbol</th><th>Reason</th></tr></thead>',
    '<thead><tr><th>Action</th><th>Symbol</th><th>Confidence</th><th>If Rotated</th><th>Reason</th></tr></thead>'
)

# Upgrade JS renderer
old_js = '''<tr>
        <td class="${x.severity||'info'}">${x.action||''}</td>
        <td>${x.symbol||''}</td>
        <td>${x.reason||''}</td>
      </tr>'''

new_js = '''<tr>
        <td class="${x.severity||'info'}">${x.action||''}</td>
        <td>${x.symbol||''}</td>
        <td>${x.confidence ?? 0}%</td>
        <td>${money(x.simulated_improvement||0)}</td>
        <td>${x.reason||''}</td>
      </tr>'''

txt = txt.replace(old_js, new_js)

txt = txt.replace(
    '"<tr><td colspan=\'3\'>No rotation suggestions yet.</td></tr>"',
    '"<tr><td colspan=\'5\'>No rotation suggestions yet.</td></tr>"'
)

# Add Ponder branch for rotation questions
if "rotation analysis" not in txt.lower():
    txt = txt.replace(
        '''} else if(q.includes("suggest") || q.includes("should") || q.includes("next")){''',
        r'''} else if(q.includes("rotation") || q.includes("rotate")){
    const rotations = lab.rotation_suggestions || [];
    if(!rotations.length){
      ans.textContent="No rotation suggestions available yet.";
      return;
    }
    const main = rotations[0] || {};
    ans.textContent=`Ponder Rotation Analysis 🐾

Primary signal:
- Action: ${main.action || "-"}
- Symbol: ${main.symbol || "-"}
- Confidence: ${main.confidence ?? 0}%
- Estimated avoided drag if rotated: ${money(main.simulated_improvement || 0)}

Reason:
${main.reason || "No reason available."}

Important:
This is suggestion-only. Do not enable auto-rotation until you have at least 15–20 closed trades and enough data to validate exits.`;

  } else if(q.includes("suggest") || q.includes("should") || q.includes("next")){'''
    )

# Add button
if "Rotation analysis?" not in txt:
    txt = txt.replace(
        '<button onclick="askPonder(\'change\')">What changed recently?</button>',
        '''<button onclick="askPonder('change')">What changed recently?</button>
      <button onclick="askPonder('rotation')">Rotation analysis?</button>'''
    )

p.write_text(txt)

print("DONE: Rotation Confidence + Simulation installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
