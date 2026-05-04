"""Research-only shadow learning signals for Ponder Invest AI."""

from datetime import datetime
from learning_shadow import log_learning_event

SHADOW_VERSION = "v2.1"

# --- NEW LEARNING CONFIG ---
SMALL_CAP_THRESHOLD = 68
SMALL_CAP_SIM_CAPITAL = 500
SMALL_CAP_MAX_POSITION = 100
DAY_TRADE_THRESHOLD = 80

SLOW_LOSER_PCT = -2.5
WEAK_PCT = -4.0
MIN_SCORE_GAP = 12
FAST_SIGNAL_SCORE = 80


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def candidate_dict(candidate):
    if isinstance(candidate, dict):
        return {
            "symbol": candidate.get("symbol", "-"),
            "score": safe_float(candidate.get("score", 0)),
            "trend": candidate.get("trend", "unknown"),
            "analyst": safe_float(candidate.get("analyst", 0)),
            "news": safe_float(candidate.get("news", 0)),
        }
    return {"symbol": "-", "score": 0, "trend": "unknown", "analyst": 0, "news": 0}


# --- NEW SMALL CAP SHADOW ---
def log_small_cap_shadow(candidates):
    for raw in candidates or []:
        c = candidate_dict(raw)
        if c["score"] >= SMALL_CAP_THRESHOLD:
            log_learning_event(
                "SHADOW_SMALL_CAP_BUY_DECISION",
                symbol=c["symbol"],
                score=c["score"],
                reason="fits small capital learning model",
                notes=f"shadow_only=true | sim_capital={SMALL_CAP_SIM_CAPITAL} | max_position={SMALL_CAP_MAX_POSITION}"
            )


# --- NEW DAY TRADE SHADOW ---
def log_day_trade_shadow(candidates):
    for raw in candidates or []:
        c = candidate_dict(raw)
        if c["score"] >= DAY_TRADE_THRESHOLD:
            log_learning_event(
                "SHADOW_DAY_TRADE_SIGNAL",
                symbol=c["symbol"],
                score=c["score"],
                reason="high momentum short-term opportunity",
                notes=f"shadow_only=true | aggressive_mode=true"
            )


# --- EXISTING LOGIC (unchanged) ---
def log_fast_signal_candidates(candidates):
    events = []
    for raw in candidates or []:
        cand = candidate_dict(raw)
        if cand["score"] < FAST_SIGNAL_SCORE:
            continue

        if cand["news"] >= 1:
            decision = "research_fast_signal_confirmed"
            reason = "Research signal: high score with catalyst confirmation."
        else:
            decision = "research_fast_signal_unconfirmed"
            reason = "Research signal: high score but weak catalyst confirmation."

        log_learning_event(
            "SHADOW_FAST_SIGNAL",
            symbol=cand["symbol"],
            score=cand["score"],
            reason=reason,
            rotation_decision=decision,
            notes=f"shadow_only=true | version={SHADOW_VERSION}"
        )
        events.append({"symbol": cand["symbol"], "decision": decision, "score": cand["score"]})
    return events


def run_shadow_learning_v2(positions=None, candidates=None, log_func=None):
    try:
        log_small_cap_shadow(candidates)
        log_day_trade_shadow(candidates)

        fast_events = log_fast_signal_candidates(candidates or [])

        if log_func:
            log_func(f"SHADOW V2 | small_cap=yes | day_trade=yes | fast={len(fast_events)}")

        return {
            "mode": "shadow_only",
            "version": SHADOW_VERSION,
            "fast_events": len(fast_events),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        try:
            log_learning_event("SHADOW_V2_ERROR", reason=str(e))
            if log_func:
                log_func(f"SHADOW V2 ERROR | {e}")
        except Exception:
            pass
        return {"mode": "shadow_only", "error": str(e)}
