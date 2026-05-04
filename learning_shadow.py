
import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/home/ubuntu/trading-bot")
MEMORY_FILE = ROOT / "learning_shadow_log.csv"
STATE_FILE = ROOT / "learning_shadow_state.json"

FIELDS = [
    "timestamp",
    "event",
    "symbol",
    "score",
    "price",
    "qty",
    "reason",
    "open_pl",
    "rotation_score",
    "rotation_decision",
    "notes"
]

def _ensure_file():
    if not MEMORY_FILE.exists():
        with MEMORY_FILE.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

def _format_extra_fields(extra_fields):
    """Convert unexpected logger keyword arguments into safe note text."""
    if not extra_fields:
        return ""
    try:
        return " | ".join(f"{key}={value}" for key, value in sorted(extra_fields.items()))
    except Exception:
        return str(extra_fields)

def log_learning_event(
    event,
    symbol="-",
    score="",
    price="",
    qty="",
    reason="",
    open_pl="",
    rotation_score="",
    rotation_decision="",
    notes="",
    **extra_fields
):
    """
    Record a shadow-learning event without ever breaking the live bot.

    The bot has multiple modules calling this logger. Accepting **extra_fields
    prevents crashes like: log_learning_event() got an unexpected keyword
    argument 'setup'. Unknown values are preserved in the notes column.
    """
    try:
        _ensure_file()

        extra_notes = _format_extra_fields(extra_fields)
        if extra_notes:
            notes = f"{notes} | {extra_notes}" if notes else extra_notes

        row = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "symbol": symbol,
            "score": score,
            "price": price,
            "qty": qty,
            "reason": reason,
            "open_pl": open_pl,
            "rotation_score": rotation_score,
            "rotation_decision": rotation_decision,
            "notes": notes
        }
        with MEMORY_FILE.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)
        return True
    except Exception:
        return False

def summarize_learning(limit=200):
    _ensure_file()
    rows = []
    try:
        with MEMORY_FILE.open("r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[-limit:]
    except Exception:
        rows = []

    counts = {}
    symbols = {}

    for r in rows:
        event = r.get("event", "UNKNOWN")
        counts[event] = counts.get(event, 0) + 1

        sym = r.get("symbol") or "-"
        if sym != "-":
            symbols.setdefault(sym, {"events": 0, "buys": 0, "sells": 0})
            symbols[sym]["events"] += 1
            if "BUY" in event:
                symbols[sym]["buys"] += 1
            if "SELL" in event:
                symbols[sym]["sells"] += 1

    return {
        "rows": rows[-50:],
        "counts": counts,
        "symbols": symbols,
        "total": len(rows),
        "mode": "shadow_only"
    }


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def summarize_learning_performance(limit=500):
    """
    Learning v2: performance-style summary.
    Shadow-only. Reads learning_shadow_log.csv.
    Does not control trades.
    """
    _ensure_file()

    try:
        with MEMORY_FILE.open("r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[-limit:]
    except Exception:
        rows = []

    total = len(rows)
    buys = [r for r in rows if "BUY_DECISION" in (r.get("event") or "")]
    skips = [r for r in rows if "SKIP_BUY" in (r.get("event") or "")]
    sells = [r for r in rows if "SELL" in (r.get("event") or "")]

    wins = []
    losses = []
    total_pnl = 0.0

    for r in sells:
        pnl = _safe_float(r.get("open_pl"))
        total_pnl += pnl
        if pnl > 0:
            wins.append(r)
        elif pnl < 0:
            losses.append(r)

    closed = len(sells)
    win_rate = round((len(wins) / closed) * 100, 2) if closed else 0
    avg_win = round(sum(_safe_float(r.get("open_pl")) for r in wins) / len(wins), 2) if wins else 0
    avg_loss = round(sum(_safe_float(r.get("open_pl")) for r in losses) / len(losses), 2) if losses else 0

    symbol_stats = {}
    for r in rows:
        sym = r.get("symbol") or "-"
        if sym == "-":
            continue
        symbol_stats.setdefault(sym, {
            "events": 0,
            "buys": 0,
            "sells": 0,
            "wins": 0,
            "losses": 0,
            "pnl": 0.0
        })

        symbol_stats[sym]["events"] += 1

        event = r.get("event") or ""
        if "BUY_DECISION" in event:
            symbol_stats[sym]["buys"] += 1
        if "SELL" in event:
            pnl = _safe_float(r.get("open_pl"))
            symbol_stats[sym]["sells"] += 1
            symbol_stats[sym]["pnl"] += pnl
            if pnl > 0:
                symbol_stats[sym]["wins"] += 1
            elif pnl < 0:
                symbol_stats[sym]["losses"] += 1

    ranked_symbols = sorted(
        symbol_stats.items(),
        key=lambda x: x[1]["pnl"],
        reverse=True
    )

    best_symbol = ranked_symbols[0][0] if ranked_symbols else "-"
    worst_symbol = ranked_symbols[-1][0] if ranked_symbols else "-"

    status = "Collecting"
    if total >= 20 and closed == 0:
        status = "Decision data ready; waiting for closed trades"
    elif closed >= 15:
        status = "Performance sample improving"
    elif closed >= 5:
        status = "Early performance sample"

    return {
        "mode": "shadow_performance",
        "status": status,
        "total_events": total,
        "buy_decisions": len(buys),
        "skips": len(skips),
        "closed_trades": closed,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "total_pnl": round(total_pnl, 2),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "best_symbol": best_symbol,
        "worst_symbol": worst_symbol,
        "symbols": symbol_stats
    }
