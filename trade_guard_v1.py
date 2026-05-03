
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
