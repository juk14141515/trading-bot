"""Research-only exit quality evaluator for Ponder Invest AI.

Reads closed sell rows from trade_history.csv and evaluates whether the recorded
exit looked early, protective, or inconclusive based on post-exit price movement.
This is a reporting module only and writes CSV/JSON research outputs.
"""

from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yfinance as yf

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
STATIC_RESEARCH = ROOT / "static" / "research"
TRADE_HISTORY = ROOT / "trade_history.csv"
OUT_CSV = RESEARCH_DATA / "exit_quality_evaluations.csv"
OUT_JSON = STATIC_RESEARCH / "exit_quality_latest.json"

WINDOWS = {"30m": 30, "60m": 60, "1d": 1440, "3d": 4320, "5d": 7200}

FIELDS = [
    "trade_id", "symbol", "entry_timestamp", "exit_timestamp", "entry_price", "exit_price",
    "qty", "pnl", "pnl_pct", "exit_reason", "holding_minutes",
    "eligible_30m", "eligible_60m", "eligible_1d", "eligible_3d", "eligible_5d",
    "post_exit_max_return_30m", "post_exit_max_return_60m", "post_exit_max_return_1d",
    "post_exit_max_return_3d", "post_exit_max_return_5d",
    "post_exit_min_return_30m", "post_exit_min_return_60m", "post_exit_min_return_1d",
    "post_exit_min_return_3d", "post_exit_min_return_5d",
    "max_favorable_after_exit", "max_adverse_after_exit", "exit_quality", "exit_score",
    "evaluation_status", "mature_windows", "pending_windows",
]


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


def utc_now() -> str:
    return utc_now_dt().isoformat(timespec="seconds")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, "", "None", "nan", "NaN"):
            return default
        return float(value)
    except Exception:
        return default


def safe_str(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def parse_timestamp(value: Any) -> Optional[datetime]:
    raw = safe_str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", errors="ignore") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def row_side(row: Dict[str, Any]) -> str:
    return safe_str(row.get("side") or row.get("action")).lower().strip()


def normalize_trade_id(symbol: str, timestamp: str) -> str:
    compact = safe_str(timestamp).replace("-", "").replace(":", "").replace(".", "")
    return f"{safe_str(symbol).upper()}-{compact or 'unknown'}"


def pair_trades(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    open_by_symbol: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    closed: List[Dict[str, Any]] = []
    for row in rows:
        symbol = safe_str(row.get("symbol")).upper().strip()
        if not symbol:
            continue
        side = row_side(row)
        if side == "buy":
            open_by_symbol[symbol].append(row)
            continue
        if side != "sell":
            continue
        matched_entry = open_by_symbol[symbol].pop(-1) if open_by_symbol[symbol] else {}
        entry_ts = safe_str(row.get("entry_timestamp") or matched_entry.get("entry_timestamp") or matched_entry.get("timestamp"))
        exit_ts = safe_str(row.get("exit_timestamp") or row.get("timestamp"))
        trade_id = safe_str(row.get("trade_id") or matched_entry.get("trade_id") or normalize_trade_id(symbol, entry_ts or exit_ts))
        entry_price = safe_float(matched_entry.get("price")) if matched_entry else None
        if entry_price is None:
            entry_price = safe_float(row.get("entry_price"))
        closed.append({
            "trade_id": trade_id,
            "symbol": symbol,
            "entry_timestamp": entry_ts,
            "exit_timestamp": exit_ts,
            "entry_price": entry_price,
            "exit_price": safe_float(row.get("price") or row.get("exit_price")),
            "qty": safe_float(row.get("qty"), 0.0),
            "pnl": safe_float(row.get("pnl")),
            "pnl_pct": safe_float(row.get("pnl_pct")),
            "exit_reason": safe_str(row.get("exit_reason") or row.get("reason") or "unknown"),
            "holding_minutes": safe_float(row.get("holding_minutes")),
        })
    return closed


def maturity_for(exit_dt: Optional[datetime], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or utc_now_dt()
    if exit_dt is None:
        flags = {label: False for label in WINDOWS}
        return {"flags": flags, "mature_windows": [], "pending_windows": list(WINDOWS.keys()), "evaluation_status": "missing_exit_timestamp"}
    age_minutes = (now - exit_dt).total_seconds() / 60
    is_future = age_minutes < 0
    flags = {label: (not is_future and age_minutes >= minutes) for label, minutes in WINDOWS.items()}
    mature = [label for label, ready in flags.items() if ready]
    pending = [label for label, ready in flags.items() if not ready]
    if is_future:
        status = "future_timestamp_pending"
    elif mature:
        status = "partially_evaluated" if pending else "fully_evaluated"
    else:
        status = "pending_maturity"
    return {"flags": flags, "mature_windows": mature, "pending_windows": pending, "evaluation_status": status}


def fetch_post_exit_path(symbol: str, exit_dt: datetime, mature_windows: List[str]):
    if not mature_windows:
        return None
    max_minutes = max(WINDOWS[label] for label in mature_windows)
    end_dt = exit_dt + timedelta(minutes=max_minutes + 60)
    try:
        return yf.Ticker(symbol).history(start=exit_dt, end=end_dt, interval="30m")
    except Exception:
        return None


def post_exit_returns(symbol: str, exit_dt: Optional[datetime], exit_price: Optional[float], maturity: Dict[str, Any]) -> Tuple[Dict[str, Optional[float]], Dict[str, Optional[float]]]:
    max_returns = {label: None for label in WINDOWS}
    min_returns = {label: None for label in WINDOWS}
    mature_windows = maturity.get("mature_windows", [])
    if exit_dt is None or exit_price is None or exit_price <= 0 or not mature_windows:
        return max_returns, min_returns
    hist = fetch_post_exit_path(symbol, exit_dt, mature_windows)
    if hist is None or hist.empty:
        return max_returns, min_returns
    for label, minutes in WINDOWS.items():
        if label not in mature_windows:
            continue
        subset = hist[hist.index <= exit_dt + timedelta(minutes=minutes)]
        if subset.empty:
            continue
        high = safe_float(subset["High"].max())
        low = safe_float(subset["Low"].min())
        if high is not None:
            max_returns[label] = round(((high - exit_price) / exit_price) * 100, 2)
        if low is not None:
            min_returns[label] = round(((low - exit_price) / exit_price) * 100, 2)
    return max_returns, min_returns


def classify_exit(max_favorable: Optional[float], max_adverse: Optional[float], pnl_pct: Optional[float], reason: str) -> Tuple[str, int]:
    favorable = max_favorable if max_favorable is not None else 0.0
    adverse = max_adverse if max_adverse is not None else 0.0
    pnl = pnl_pct if pnl_pct is not None else 0.0
    reason_l = reason.lower()
    if favorable >= 5:
        return "likely_too_early_major_upside_left", 35
    if favorable >= 3:
        return "possibly_too_early", 50
    if adverse <= -3 and favorable < 2:
        return "protective_exit_helped", 85
    if adverse <= -1.5 and favorable < 2:
        return "exit_probably_helped", 75
    if -1.0 <= adverse <= 0 and favorable <= 1.5:
        return "reasonable_exit", 70
    if "trailing" in reason_l and favorable >= 2:
        return "trailing_stop_may_be_tight", 55
    if pnl < 0 and favorable >= 2:
        return "loss_exit_before_rebound", 45
    return "neutral_inconclusive", 60


def evaluate_exit(trade: Dict[str, Any]) -> Dict[str, Any]:
    exit_dt = parse_timestamp(trade.get("exit_timestamp"))
    maturity = maturity_for(exit_dt)
    max_ret, min_ret = post_exit_returns(trade["symbol"], exit_dt, safe_float(trade.get("exit_price")), maturity)
    mature_max = [v for v in max_ret.values() if v is not None]
    mature_min = [v for v in min_ret.values() if v is not None]
    max_favorable = round(max(mature_max), 2) if mature_max else None
    max_adverse = round(min(mature_min), 2) if mature_min else None
    quality, score = classify_exit(max_favorable, max_adverse, safe_float(trade.get("pnl_pct")), trade.get("exit_reason", ""))
    return {
        **trade,
        "eligible_30m": maturity["flags"].get("30m", False),
        "eligible_60m": maturity["flags"].get("60m", False),
        "eligible_1d": maturity["flags"].get("1d", False),
        "eligible_3d": maturity["flags"].get("3d", False),
        "eligible_5d": maturity["flags"].get("5d", False),
        "post_exit_max_return_30m": max_ret.get("30m", ""),
        "post_exit_max_return_60m": max_ret.get("60m", ""),
        "post_exit_max_return_1d": max_ret.get("1d", ""),
        "post_exit_max_return_3d": max_ret.get("3d", ""),
        "post_exit_max_return_5d": max_ret.get("5d", ""),
        "post_exit_min_return_30m": min_ret.get("30m", ""),
        "post_exit_min_return_60m": min_ret.get("60m", ""),
        "post_exit_min_return_1d": min_ret.get("1d", ""),
        "post_exit_min_return_3d": min_ret.get("3d", ""),
        "post_exit_min_return_5d": min_ret.get("5d", ""),
        "max_favorable_after_exit": max_favorable if max_favorable is not None else "",
        "max_adverse_after_exit": max_adverse if max_adverse is not None else "",
        "exit_quality": quality,
        "exit_score": score,
        "evaluation_status": maturity["evaluation_status"],
        "mature_windows": ",".join(maturity["mature_windows"]),
        "pending_windows": ",".join(maturity["pending_windows"]),
    }


def mature_evaluations(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if r.get("max_favorable_after_exit") not in (None, "")]


def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    mature = mature_evaluations(rows)
    quality_counts = Counter(r.get("exit_quality", "unknown") for r in mature)
    by_reason: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in mature:
        by_reason[row.get("exit_reason", "unknown")].append(row)
    avg_score = round(sum(safe_float(r.get("exit_score"), 0) or 0 for r in mature) / max(len(mature), 1), 2) if mature else 0
    avg_favorable = round(sum(safe_float(r.get("max_favorable_after_exit"), 0) or 0 for r in mature) / max(len(mature), 1), 2) if mature else 0
    avg_adverse = round(sum(safe_float(r.get("max_adverse_after_exit"), 0) or 0 for r in mature) / max(len(mature), 1), 2) if mature else 0
    reason_stats = {}
    for reason, items in by_reason.items():
        reason_stats[reason] = {
            "count": len(items),
            "avg_exit_score": round(sum(safe_float(r.get("exit_score"), 0) or 0 for r in items) / max(len(items), 1), 2),
            "avg_favorable_after_exit": round(sum(safe_float(r.get("max_favorable_after_exit"), 0) or 0 for r in items) / max(len(items), 1), 2),
            "avg_adverse_after_exit": round(sum(safe_float(r.get("max_adverse_after_exit"), 0) or 0 for r in items) / max(len(items), 1), 2),
        }
    confidence = "HIGH" if len(mature) >= 50 else "MEDIUM" if len(mature) >= 15 else "LOW"
    if not mature:
        verdict = "insufficient_mature_exits"
    elif avg_score >= 75:
        verdict = "exits_generally_helping"
    elif avg_score >= 60:
        verdict = "exits_mixed_or_neutral"
    else:
        verdict = "exit_quality_needs_review"
    return {
        "total_closed_exits": len(rows),
        "mature_exits": len(mature),
        "pending_exits": max(0, len(rows) - len(mature)),
        "confidence": confidence,
        "avg_exit_score": avg_score,
        "avg_favorable_after_exit_pct": avg_favorable,
        "avg_adverse_after_exit_pct": avg_adverse,
        "quality_counts": dict(quality_counts),
        "by_exit_reason": reason_stats,
        "verdict": verdict,
    }


def main() -> Dict[str, Any]:
    started = time.time()
    RESEARCH_DATA.mkdir(parents=True, exist_ok=True)
    STATIC_RESEARCH.mkdir(parents=True, exist_ok=True)
    closed = pair_trades(read_csv(TRADE_HISTORY))
    evaluated = []
    for trade in closed:
        evaluated.append(evaluate_exit(trade))
        time.sleep(0.2)
    write_csv(evaluated, OUT_CSV)
    mature = mature_evaluations(evaluated)
    payload = {
        "status": "ok",
        "version": "exit_quality_evaluator_v1",
        "updated_at": utc_now(),
        "runtime_ms": int((time.time() - started) * 1000),
        "source": "exit_quality_evaluator",
        "records": len(evaluated),
        "mature_records": len(mature),
        "pending_records": max(0, len(evaluated) - len(mature)),
        "summary": build_summary(evaluated),
        "worst_exits": sorted(mature, key=lambda r: safe_float(r.get("exit_score"), 999) or 999)[:10],
        "best_protective_exits": sorted(mature, key=lambda r: safe_float(r.get("exit_score"), 0) or 0, reverse=True)[:10],
        "pending_examples": [r for r in evaluated if r.get("evaluation_status") in {"pending_maturity", "future_timestamp_pending"}][:10],
        "notes": [
            "Research-only evaluation of completed sell exits.",
            "High post-exit upside suggests possible early exit; strong post-exit downside suggests the exit protected capital.",
            "This module only writes research outputs.",
        ],
        "safety": {"read_only": True, "automation_allowed": False},
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
