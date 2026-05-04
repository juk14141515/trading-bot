"""Research-only shadow learning signals for Ponder Invest AI."""

from datetime import datetime
from learning_shadow import log_learning_event

SHADOW_VERSION = "v2.0"
SLOW_LOSER_PCT = -2.5
WEAK_PCT = -4.0
MIN_SCORE_GAP = 12
FAST_SIGNAL_SCORE = 80


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def position_dict(position):
    symbol = getattr(position, "symbol", "-")
    qty = abs(safe_float(getattr(position, "qty", 0)))
    entry = safe_float(getattr(position, "avg_entry_price", 0))
    current = safe_float(getattr(position, "current_price", 0))
    market_value = safe_float(getattr(position, "market_value", 0))
    open_pl = safe_float(getattr(position, "unrealized_pl", 0))
    open_pl_pct = safe_float(getattr(position, "unrealized_plpc", 0)) * 100

    if entry > 0 and current > 0:
        open_pl_pct = ((current - entry) / entry) * 100

    return {
        "symbol": symbol,
        "qty": qty,
        "entry": entry,
        "current": current,
        "market_value": market_value,
        "open_pl": open_pl,
        "open_pl_pct": round(open_pl_pct, 3),
    }


def candidate_dict(candidate):
    if isinstance(candidate, dict):
        return {
            "symbol": candidate.get("symbol", "-"),
            "score": safe_float(candidate.get("score", 0)),
            "trend": candidate.get("trend", "unknown"),
            "analyst": safe_float(candidate.get("analyst", 0)),
            "news": safe_float(candidate.get("news", 0)),
        }
    try:
        symbol, score = candidate
        return {"symbol": symbol, "score": safe_float(score), "trend": "unknown", "analyst": 0, "news": 0}
    except Exception:
        return {"symbol": "-", "score": 0, "trend": "unknown", "analyst": 0, "news": 0}


def position_strength(pos):
    pl_pct = safe_float(pos.get("open_pl_pct"))
    value = safe_float(pos.get("market_value"))
    score = 50 + (pl_pct * 4)
    if value <= 0:
        score -= 10
    if pl_pct <= SLOW_LOSER_PCT:
        score -= 15
    if pl_pct <= WEAK_PCT:
        score -= 20
    return round(max(0, min(100, score)), 2)


def log_shadow_sell_signals(positions):
    events = []
    for raw in positions or []:
        pos = position_dict(raw)
        pl_pct = pos["open_pl_pct"]
        strength = position_strength(pos)

        if pl_pct <= WEAK_PCT:
            decision = "research_exit_weak"
            reason = "Research signal: position is materially weak."
        elif pl_pct <= SLOW_LOSER_PCT:
            decision = "research_exit_slow_loser"
            reason = "Research signal: position is drifting lower."
        elif pl_pct >= 6:
            decision = "research_hold_winner"
            reason = "Research signal: position is working."
        else:
            decision = "research_hold_neutral"
            reason = "Research signal: no exit pressure."

        log_learning_event(
            "SHADOW_SELL_V2_SIGNAL",
            symbol=pos["symbol"],
            score=strength,
            qty=pos["qty"],
            reason=reason,
            open_pl=pos["open_pl"],
            rotation_decision=decision,
            notes=f"shadow_only=true | version={SHADOW_VERSION} | pl_pct={pl_pct} | entry={pos['entry']} | current={pos['current']}",
        )
        events.append({"symbol": pos["symbol"], "decision": decision, "score": strength, "pl_pct": pl_pct})
    return events


def log_capital_efficiency_signal(positions, candidates):
    pos_list = [position_dict(p) for p in (positions or [])]
    cand_list = [candidate_dict(c) for c in (candidates or [])]
    if not pos_list or not cand_list:
        return None

    weakest = sorted(pos_list, key=position_strength)[0]
    best = sorted(cand_list, key=lambda c: c["score"], reverse=True)[0]
    weak_score = position_strength(weakest)
    gap = round(best["score"] - weak_score, 2)

    if gap >= MIN_SCORE_GAP:
        decision = "research_candidate_stronger"
        reason = "Research signal: candidate is stronger than weakest current holding."
    else:
        decision = "research_no_clear_edge"
        reason = "Research signal: candidate edge is not large enough."

    log_learning_event(
        "SHADOW_CAPITAL_EFFICIENCY",
        symbol=best["symbol"],
        score=best["score"],
        reason=reason,
        open_pl=weakest.get("open_pl", 0),
        rotation_score=gap,
        rotation_decision=decision,
        notes=f"shadow_only=true | version={SHADOW_VERSION} | weakest={weakest['symbol']} | weakest_score={weak_score} | best_candidate={best['symbol']}",
    )
    return {"decision": decision, "weakest": weakest["symbol"], "best": best["symbol"], "gap": gap}


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
            notes=f"shadow_only=true | version={SHADOW_VERSION} | sim_capital=500 | trend={cand['trend']} | analyst={cand['analyst']} | news={cand['news']}",
        )
        events.append({"symbol": cand["symbol"], "decision": decision, "score": cand["score"]})
    return events


def run_shadow_learning_v2(positions=None, candidates=None, log_func=None):
    try:
        sell_events = log_shadow_sell_signals(positions or [])
        efficiency = log_capital_efficiency_signal(positions or [], candidates or [])
        fast_events = log_fast_signal_candidates(candidates or [])
        if log_func:
            log_func(f"SHADOW V2 | sell={len(sell_events)} | capital={'yes' if efficiency else 'no'} | fast={len(fast_events)}")
        return {
            "mode": "shadow_only",
            "version": SHADOW_VERSION,
            "sell_events": len(sell_events),
            "capital_efficiency": efficiency,
            "fast_events": len(fast_events),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        try:
            log_learning_event("SHADOW_V2_ERROR", reason=str(e), notes=f"shadow_only=true | version={SHADOW_VERSION}")
            if log_func:
                log_func(f"SHADOW V2 ERROR | {e}")
        except Exception:
            pass
        return {"mode": "shadow_only", "error": str(e)}
