from pathlib import Path
from datetime import datetime

BOT = Path("bot.py")
ROTATION = Path("rotation_manager.py")

backup = Path(f"bot_backup_before_rotation_inject_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(BOT.read_text())

ROTATION.write_text(r'''
def get_position_score(position):
    """
    Lower score = weaker position.
    Uses unrealized P/L percentage and current trend.
    """
    try:
        symbol = position.symbol
        entry = float(position.avg_entry_price)
        current = float(position.current_price)
        change_pct = (current - entry) / entry

        score = 50

        # P/L impact
        score += change_pct * 100

        # Weakness penalties
        if change_pct <= -0.03:
            score -= 25
        elif change_pct <= -0.015:
            score -= 15

        # Strength bonus
        if change_pct >= 0.02:
            score += 10

        return {
            "symbol": symbol,
            "score": round(score, 2),
            "change_pct": change_pct,
            "qty": abs(float(position.qty)),
        }

    except Exception:
        return {
            "symbol": getattr(position, "symbol", "UNKNOWN"),
            "score": 999,
            "change_pct": 0,
            "qty": 0,
        }


def find_weakest_position(positions):
    if not positions:
        return None

    ranked = [get_position_score(p) for p in positions]
    ranked.sort(key=lambda x: x["score"])
    return ranked[0]


def should_rotate(weak_position, new_candidate_score, min_new_score=70, required_edge=15):
    """
    Rotate only when:
    - candidate score is strong enough
    - weakest position is meaningfully weak
    - new candidate is clearly better
    """
    if not weak_position:
        return False, "no weak position"

    weak_score = weak_position["score"]
    weak_symbol = weak_position["symbol"]
    weak_change = weak_position["change_pct"]

    if new_candidate_score < min_new_score:
        return False, f"candidate score too low: {new_candidate_score}"

    if weak_change > -0.01 and weak_score > 45:
        return False, f"{weak_symbol} not weak enough"

    if new_candidate_score < weak_score + required_edge:
        return False, f"candidate edge too small vs {weak_symbol}"

    return True, f"rotate out of {weak_symbol}"
''')

text = BOT.read_text()

if "from rotation_manager import find_weakest_position, should_rotate" not in text:
    text = text.replace(
        "from small_cap_scanner import get_small_cap_candidates",
        "from small_cap_scanner import get_small_cap_candidates\nfrom rotation_manager import find_weakest_position, should_rotate"
    )

old = '''    current_positions = len(get_positions())
    slots_available = MAX_POSITIONS - current_positions

    if slots_available <= 0:
        log("No buys | max positions reached")
        return
'''

new = '''    positions = get_positions()
    current_positions = len(positions)
    slots_available = MAX_POSITIONS - current_positions
    rotation_mode = False
    weakest_position = None

    if slots_available <= 0:
        weakest_position = find_weakest_position(positions)
        rotation_mode = True
        log(f"ROTATION CHECK | max positions reached | weakest={weakest_position}")
        slots_available = 1
'''

if old not in text:
    raise SystemExit("Could not find max-position block. bot.py was not changed.")

text = text.replace(old, new)

old2 = '''    for symbol, score in candidates[:slots_available]:
        final_score = score

        allowed, reason = can_trade(symbol, final_score)
'''

new2 = '''    for symbol, score in candidates[:slots_available]:
        final_score = score

        if rotation_mode:
            rotate_ok, rotate_reason = should_rotate(weakest_position, final_score)
            if not rotate_ok:
                log(f"NO ROTATION | {symbol} | {rotate_reason}")
                continue

            log(f"ROTATION APPROVED | sell={weakest_position['symbol']} | buy={symbol} | score={final_score} | reason={rotate_reason}")
            sell(weakest_position["symbol"], weakest_position["qty"], f"rotation into {symbol}")
            notify_discord(f"🔁 ROTATION | Sold {weakest_position['symbol']} to buy {symbol} | score={final_score}")
            return

        allowed, reason = can_trade(symbol, final_score)
'''

if old2 not in text:
    raise SystemExit("Could not find candidate buy loop. bot.py was not changed.")

text = text.replace(old2, new2)

BOT.write_text(text)

print(f"✅ Rotation system injected.")
print(f"✅ Backup created: {backup}")
print("Next run:")
print("python3 -m py_compile bot.py rotation_manager.py")
print("sudo systemctl restart tradebot")
