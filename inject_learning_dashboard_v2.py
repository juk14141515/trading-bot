from pathlib import Path
from datetime import datetime

BOT = Path("bot.py")
WEB = Path("web_dashboard.py")
ADAPTIVE = Path("adaptive_learning.py")

bot = BOT.read_text()
web = WEB.read_text()
adaptive = ADAPTIVE.read_text()

BOT.write_text(bot)
Path(f"bot_backup_learning_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py").write_text(bot)
Path(f"web_dashboard_backup_learning_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py").write_text(web)
Path(f"adaptive_learning_backup_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py").write_text(adaptive)

# --- adaptive learning: add outcome summary ---
if "def get_win_loss_summary" not in adaptive:
    adaptive += r'''

def get_win_loss_summary():
    trades = _closed_trades()

    wins = [t for t in trades if t["pnl_float"] > 0]
    losses = [t for t in trades if t["pnl_float"] < 0]

    return {
        "closed_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round((len(wins) / len(trades)) * 100, 2) if trades else 0,
        "net_pnl": round(sum(t["pnl_float"] for t in trades), 2) if trades else 0,
    }
'''
ADAPTIVE.write_text(adaptive)

# --- bot imports ---
if "get_win_loss_summary" not in bot:
    bot = bot.replace(
        "from adaptive_learning import apply_adaptive_score, get_performance_summary",
        "from adaptive_learning import apply_adaptive_score, get_performance_summary, get_win_loss_summary"
    )

# --- minimum candidate guarantee ---
old_candidates = '''    candidates.sort(key=lambda x: x[1], reverse=True)

    for symbol, score in candidates[:slots_available]:
'''

new_candidates = '''    candidates.sort(key=lambda x: x[1], reverse=True)

    if len(candidates) == 0 and enhanced:
        log(f"LEARNING MODE | no scored candidates | using enhanced fallback={enhanced[:2]}")
        for fallback_symbol in enhanced[:2]:
            candidates.append((fallback_symbol, 65))

    for symbol, score in candidates[:slots_available]:
'''

if old_candidates in bot:
    bot = bot.replace(old_candidates, new_candidates, 1)
else:
    print("WARNING: candidate fallback patch point not found")

# --- confidence logging ---
old_adaptive_log = '''        log(f"ADAPTIVE | {symbol} | {adaptive_reason}")
'''

new_adaptive_log = '''        log(f"ADAPTIVE | {symbol} | {adaptive_reason}")
        log(f"CONFIDENCE | {symbol} | base_score={score} | final_score={final_score}")
'''

if old_adaptive_log in bot:
    bot = bot.replace(old_adaptive_log, new_adaptive_log, 1)
else:
    print("WARNING: confidence log patch point not found")

# --- update bot status with learning summary ---
old_status = '''        save_status({
            "market_trend": spy_trend,
            "top_candidates": candidates[:5],
            "positions": len(get_positions()),
            "slots_available": slots_available,
            "last_action": f"BUY {symbol}",
            "last_score": final_score
        })
'''

new_status = '''        learning_summary = get_win_loss_summary()

        save_status({
            "market_trend": spy_trend,
            "top_candidates": candidates[:5],
            "positions": len(get_positions()),
            "slots_available": slots_available,
            "last_action": f"BUY {symbol}",
            "last_score": final_score,
            "learning_summary": learning_summary
        })
'''

if old_status in bot:
    bot = bot.replace(old_status, new_status, 1)
else:
    print("WARNING: status learning summary patch point not found")

BOT.write_text(bot)

# --- dashboard: rename with Ponder touch ---
web = web.replace(
    "Advanced autonomous paper-trading command center · refreshes every 5 seconds",
    "Ponder-powered autonomous trading command center · refreshes every 5 seconds"
)

web = web.replace(
    '<div class="brand">Ponder Invest <span>AI</span></div>',
    '<div class="brand">Ponder Invest <span>AI</span> 🐾</div>'
)

# --- dashboard: add learning cards if template found ---
card_marker = '''<div class="card"><h3>Adaptive Events</h3><div class="big">{{ adaptive_count }}</div><p class="muted">Learning adjustments</p></div>
</div>'''

learning_cards = '''<div class="card"><h3>Adaptive Events</h3><div class="big">{{ adaptive_count }}</div><p class="muted">Learning adjustments</p></div>
<div class="card"><h3>Closed Win Rate</h3><div class="big">{{ learning_summary.get("win_rate", 0) }}%</div><p class="muted">{{ learning_summary.get("wins", 0) }} wins · {{ learning_summary.get("losses", 0) }} losses</p></div>
<div class="card"><h3>Closed Net P/L</h3><div class="big {{ 'green' if learning_summary.get('net_pnl', 0) >= 0 else 'red' }}">{{ money(learning_summary.get("net_pnl", 0)) }}</div><p class="muted">{{ learning_summary.get("closed_trades", 0) }} closed trades tracked</p></div>
</div>'''

if card_marker in web:
    web = web.replace(card_marker, learning_cards, 1)
else:
    print("WARNING: dashboard learning card marker not found")

# --- dashboard: pass learning_summary ---
if "learning_summary = status_data.get(\"learning_summary\"" not in web:
    web = web.replace(
        'summary = status_data.get("summary", {})',
        'summary = status_data.get("summary", {})\n    learning_summary = status_data.get("learning_summary", {"closed_trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "net_pnl": 0})'
    )

if "learning_summary=learning_summary," not in web:
    web = web.replace(
        "money=money,",
        "learning_summary=learning_summary,\n        money=money,"
    )

WEB.write_text(web)

print("✅ Learning dashboard v2 installed")
print("✅ Added win/loss summary")
print("✅ Added minimum candidate guarantee")
print("✅ Added confidence logging")
print("✅ Added Ponder 🐾 brand touch")
print("Now run:")
print("python3 -m py_compile bot.py web_dashboard.py adaptive_learning.py")
print("sudo systemctl restart tradebot")
print("sudo systemctl restart tradebot-dashboard")
