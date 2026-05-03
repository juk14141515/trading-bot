import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

TRADE_LOG_FILE = "trade_history.csv"

# Keep the original columns first so older dashboard/evaluator code remains compatible.
FIELDS = [
    "timestamp",
    "symbol",
    "side",
    "qty",
    "price",
    "reason",
    "score",
    "pnl",
    "pnl_pct",
    # Learning/memory columns added for strategy analysis.
    "trade_id",
    "entry_timestamp",
    "exit_timestamp",
    "holding_minutes",
    "entry_reason",
    "exit_reason",
    "strategy",
    "setup",
    "notes",
]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _read_rows() -> List[Dict[str, Any]]:
    if not os.path.exists(TRADE_LOG_FILE):
        return []
    try:
        with open(TRADE_LOG_FILE, "r", newline="", errors="ignore") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _trade_id(symbol: str, timestamp: str) -> str:
    clean_symbol = str(symbol or "UNK").upper().replace(" ", "")
    compact_ts = str(timestamp).replace("-", "").replace(":", "").replace(".", "")
    return f"{clean_symbol}-{compact_ts}"


def _parse_timestamp(value: Any) -> Optional[datetime]:
    try:
        if not value:
            return None
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _latest_open_entry(symbol: str) -> Dict[str, Any]:
    """Best-effort match to the latest buy row for a symbol.

    This does not change execution behavior. It only enriches sell rows with
    entry timestamp/reason/trade_id when the data exists.
    """
    rows = _read_rows()
    symbol = str(symbol or "").upper()
    buys: List[Dict[str, Any]] = []
    sells_after: List[Dict[str, Any]] = []

    for row in rows:
        if str(row.get("symbol") or "").upper() != symbol:
            continue
        side = str(row.get("side") or row.get("action") or "").lower()
        if side == "buy":
            buys.append(row)
        elif side == "sell":
            sells_after.append(row)

    if not buys:
        return {}

    # If there are more buys than sells, the last buy is likely still open.
    # Otherwise still return the latest buy as a fallback for learning context.
    return buys[-1]


def _holding_minutes(entry_timestamp: Any, exit_timestamp: Any) -> Optional[float]:
    entry_dt = _parse_timestamp(entry_timestamp)
    exit_dt = _parse_timestamp(exit_timestamp)
    if not entry_dt or not exit_dt:
        return None
    minutes = (exit_dt - entry_dt).total_seconds() / 60
    if minutes < 0:
        return None
    return round(minutes, 2)


def record_trade(
    symbol,
    side,
    qty,
    price,
    reason="",
    score=None,
    pnl=None,
    pnl_pct=None,
    trade_id=None,
    entry_timestamp=None,
    exit_timestamp=None,
    holding_minutes=None,
    entry_reason=None,
    exit_reason=None,
    strategy=None,
    setup=None,
    notes=None,
):
    """Append a trade memory row.

    Backward compatible with the old record_trade(symbol, side, qty, price,
    reason, score, pnl, pnl_pct) calls. New optional fields give the learning
    system enough structure to evaluate closed trades later.
    """
    file_exists = os.path.exists(TRADE_LOG_FILE)
    timestamp = _now_iso()
    normalized_side = str(side or "").lower()

    if normalized_side == "buy":
        entry_timestamp = entry_timestamp or timestamp
        entry_reason = entry_reason or reason
        trade_id = trade_id or _trade_id(symbol, entry_timestamp)
    elif normalized_side == "sell":
        matched_entry = _latest_open_entry(symbol)
        entry_timestamp = entry_timestamp or matched_entry.get("entry_timestamp") or matched_entry.get("timestamp")
        entry_reason = entry_reason or matched_entry.get("entry_reason") or matched_entry.get("reason")
        trade_id = trade_id or matched_entry.get("trade_id") or _trade_id(symbol, entry_timestamp or timestamp)
        exit_timestamp = exit_timestamp or timestamp
        exit_reason = exit_reason or reason
        holding_minutes = holding_minutes if holding_minutes is not None else _holding_minutes(entry_timestamp, exit_timestamp)
    else:
        trade_id = trade_id or _trade_id(symbol, timestamp)

    row = {
        "timestamp": timestamp,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "price": price,
        "reason": reason,
        "score": score,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "trade_id": trade_id,
        "entry_timestamp": entry_timestamp,
        "exit_timestamp": exit_timestamp,
        "holding_minutes": holding_minutes,
        "entry_reason": entry_reason,
        "exit_reason": exit_reason,
        "strategy": strategy or "current_bot",
        "setup": setup or "current_bot",
        "notes": notes,
    }

    with open(TRADE_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def recent_trade_count_today():
    if not os.path.exists(TRADE_LOG_FILE):
        return 0

    today = datetime.now().date().isoformat()
    count = 0

    with open(TRADE_LOG_FILE, "r", newline="", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row.get("timestamp", "")).startswith(today):
                count += 1

    return count


def symbol_traded_today(symbol):
    if not os.path.exists(TRADE_LOG_FILE):
        return False

    today = datetime.now().date().isoformat()
    symbol = str(symbol or "").upper()

    with open(TRADE_LOG_FILE, "r", newline="", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row.get("timestamp", "")).startswith(today) and str(row.get("symbol", "")).upper() == symbol:
                return True

    return False


def summarize_trade_memory() -> Dict[str, Any]:
    """Small helper for research modules and dashboards."""
    rows = _read_rows()
    closed = [
        row for row in rows
        if str(row.get("side") or row.get("action") or "").lower() == "sell"
        and (_safe_float(row.get("pnl")) is not None or _safe_float(row.get("pnl_pct")) is not None)
    ]
    wins = [row for row in closed if (_safe_float(row.get("pnl"), 0) or 0) > 0 or (_safe_float(row.get("pnl_pct"), 0) or 0) > 0]
    losses = [row for row in closed if (_safe_float(row.get("pnl"), 0) or 0) < 0 or (_safe_float(row.get("pnl_pct"), 0) or 0) < 0]
    return {
        "total_rows": len(rows),
        "closed_trades": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round((len(wins) / len(closed)) * 100, 2) if closed else None,
    }


if __name__ == "__main__":
    print(summarize_trade_memory())
