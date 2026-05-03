from pathlib import Path
from datetime import datetime
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_trade_logic_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("bot.py")
backup("rotation_manager.py")
backup("profit_ops_routes.py")

# ----------------------------
# 1. Bad trade protection module
# ----------------------------
(ROOT / "trade_guard_v1.py").write_text(r'''
import os

BAD_TRADE_GUARD_ENABLED = os.getenv("BAD_TRADE_GUARD_ENABLED", "true").lower() == "true"

# Conservative defaults for early paper-trading data collection
FAST_CUT_LOSS_PCT = float(os.getenv("FAST_CUT_LOSS_PCT", "-3.0"))
WEAK_CUT_LOSS_PCT = float(os.getenv("WEAK_CUT_LOSS_PCT", "-2.0"))
WEAK_POSITION_SCORE = float(os.getenv("WEAK_POSITION_SCORE", "25"))

def should_force_exit(symbol, pnl_pct, position_score=None):
    """
    pnl_pct should be percent, e.g. -3.2 not -0.032.
    position_score is optional.
    """
    if not BAD_TRADE_GUARD_ENABLED:
        return False, "guard disabled"

    try:
        pnl_pct = float(pnl_pct)
    except Exception:
        return False, "invalid pnl_pct"

    try:
        position_score = float(position_score) if position_score is not None else None
    except Exception:
        position_score = None

    # Hard emergency-style paper-trading cut
    if pnl_pct <= FAST_CUT_LOSS_PCT:
        return True, f"fast_cut_loss_{pnl_pct:.2f}%"

    # Softer rule: only cut if loser is also weak
    if position_score is not None:
        if pnl_pct <= WEAK_CUT_LOSS_PCT and position_score <= WEAK_POSITION_SCORE:
            return True, f"weak_loser_cut_{pnl_pct:.2f}%_score_{position_score:.1f}"

    return False, "hold"
''')

# ----------------------------
# 2. Safer rotation tuning module
# ----------------------------
(ROOT / "rotation_tuner_v1.py").write_text(r'''
import os

ROTATION_TUNER_ENABLED = os.getenv("ROTATION_TUNER_ENABLED", "true").lower() == "true"

# Candidate must beat weakest by this much
MIN_ROTATION_EDGE = float(os.getenv("MIN_ROTATION_EDGE", "15"))

# Don't rotate out if current position is green unless replacement is very strong
PROTECT_WINNER_PNL_PCT = float(os.getenv("PROTECT_WINNER_PNL_PCT", "1.0"))
WINNER_ROTATION_EDGE = float(os.getenv("WINNER_ROTATION_EDGE", "25"))

def approve_rotation(weakest_position, candidate_symbol, candidate_score):
    if not ROTATION_TUNER_ENABLED:
        return True, "rotation tuner disabled"

    if not weakest_position:
        return False, "no weakest position"

    try:
        current_score = float(weakest_position.get("score", 0))
    except Exception:
        current_score = 0

    try:
        candidate_score = float(candidate_score)
    except Exception:
        return False, "invalid candidate score"

    try:
        pnl_pct = float(weakest_position.get("pnl_pct", 0))
    except Exception:
        pnl_pct = 0

    edge = candidate_score - current_score

    if edge < MIN_ROTATION_EDGE:
        return False, f"rotation edge too small | edge={edge:.1f} required={MIN_ROTATION_EDGE}"

    if pnl_pct > PROTECT_WINNER_PNL_PCT and edge < WINNER_ROTATION_EDGE:
        return False, f"winner protected | pnl_pct={pnl_pct:.2f} edge={edge:.1f}"

    return True, f"rotation approved | edge={edge:.1f} pnl_pct={pnl_pct:.2f}"
''')

# ----------------------------
# 3. Patch bot.py imports
# ----------------------------
bot_path = ROOT / "bot.py"
txt = bot_path.read_text()

if "trade_guard_v1" not in txt:
    txt = txt.replace(
        "from rotation_manager import find_weakest_position, should_rotate",
        "from rotation_manager import find_weakest_position, should_rotate\nfrom trade_guard_v1 import should_force_exit\nfrom rotation_tuner_v1 import approve_rotation"
    )

# ----------------------------
# 4. Patch manage_existing_positions with force exit
# ----------------------------
if "TRADE GUARD V1" not in txt:
    pattern = r"(def manage_existing_positions\(\):\n\s+positions = get_positions\(\)\n\s+for p in positions:\n\s+symbol = p\.symbol\n)"
    m = re.search(pattern, txt)
    if not m:
        print("WARNING: Could not find exact manage_existing_positions block. No force-exit patch applied.")
    else:
        insert = m.group(1) + r'''        # TRADE GUARD V1: conservative fast loser protection
        try:
            qty = float(p.qty)
            pnl_pct = float(p.unrealized_plpc) * 100
            guard_exit, guard_reason = should_force_exit(symbol, pnl_pct)
            if guard_exit:
                log(f"TRADE GUARD | FORCE EXIT | {symbol} | pnl_pct={pnl_pct:.2f}% | reason={guard_reason}")
                sell(symbol, qty, guard_reason)
                continue
        except Exception as e:
            log(f"TRADE GUARD | error | {symbol} | {e}")

'''
        txt = txt[:m.start()] + insert + txt[m.end():]

# ----------------------------
# 5. Patch rotation approval with tuner
# ----------------------------
if "ROTATION TUNER V1" not in txt:
    old = '''        if rotation_mode:
            rotate_ok, rotate_reason = should_rotate(weakest_position, final_score)

            if not rotate_ok:
                log(f"NO ROTATION | {symbol} | score={final_score} | reason={rotate_reason}")
                continue

            log(f"ROTATION APPROVED | replacing={weakest_position['symbol']} | new={symbol} | score={final_score} | reason={rotate_reason}")
            sell(weakest_position["symbol"], weakest_position["qty"], f"rotation into {symbol}")
            notify_discord(f"🔁 ROTATION | Sold {weakest_position['symbol']} to buy {symbol} | score={final_score}")'''
    new = '''        if rotation_mode:
            rotate_ok, rotate_reason = should_rotate(weakest_position, final_score)

            # ROTATION TUNER V1: require stronger edge before replacing a holding
            tuner_ok, tuner_reason = approve_rotation(weakest_position, symbol, final_score)

            if not rotate_ok or not tuner_ok:
                log(f"NO ROTATION | {symbol} | score={final_score} | reason={rotate_reason} | tuner={tuner_reason}")
                continue

            log(f"ROTATION APPROVED | replacing={weakest_position['symbol']} | new={symbol} | score={final_score} | reason={rotate_reason} | tuner={tuner_reason}")
            sell(weakest_position["symbol"], weakest_position["qty"], f"rotation into {symbol}")
            notify_discord(f"🔁 ROTATION | Sold {weakest_position['symbol']} to buy {symbol} | score={final_score}")'''
    if old in txt:
        txt = txt.replace(old, new)
    else:
        print("WARNING: Could not find exact rotation block. No rotation tuner patch applied.")

bot_path.write_text(txt)

# ----------------------------
# 6. Patch Profit Ops chart smoothing
# ----------------------------
routes_path = ROOT / "profit_ops_routes.py"
if routes_path.exists():
    rtxt = routes_path.read_text()

    if "tension:.35" not in rtxt:
        rtxt = rtxt.replace("tension:.25", "tension:.35")
        rtxt = rtxt.replace("tension: .25", "tension:.35")

    # Slightly cleaner chart behavior
    if "pointRadius:2" not in rtxt:
        rtxt = rtxt.replace(
            "{label:\"Portfolio Value\",data:eq.map(x=>x.portfolio_value),tension:.35}",
            "{label:\"Portfolio Value\",data:eq.map(x=>x.portfolio_value),tension:.35,pointRadius:2}"
        )
        rtxt = rtxt.replace(
            "{label:\"Buying Power\",data:eq.map(x=>x.buying_power),tension:.35}",
            "{label:\"Buying Power\",data:eq.map(x=>x.buying_power),tension:.35,pointRadius:2}"
        )
        rtxt = rtxt.replace(
            "{label:\"Open P/L\",data:eq.map(x=>x.open_pl),tension:.35,yAxisID:\"y1\"}",
            "{label:\"Open P/L\",data:eq.map(x=>x.open_pl),tension:.35,pointRadius:2,yAxisID:\"y1\"}"
        )

    routes_path.write_text(rtxt)

print("DONE: Trade Logic V1 installed")
print()
print("What changed:")
print("- Added trade_guard_v1.py conservative loser protection")
print("- Added rotation_tuner_v1.py safer rotation approval")
print("- Patched bot.py lightly")
print("- Smoothed Profit Ops charts")
print()
print("Next commands:")
print("python3 -m py_compile bot.py trade_guard_v1.py rotation_tuner_v1.py profit_ops_routes.py")
print("sudo systemctl restart tradebot")
print("sudo systemctl restart tradebot-dashboard")
print("grep -n \"TRADE GUARD\\|ROTATION TUNER\\|FORCE EXIT\\|NO ROTATION\\|ROTATION APPROVED\" log.txt | tail -50")
