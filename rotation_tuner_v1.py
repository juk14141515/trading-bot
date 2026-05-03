
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
