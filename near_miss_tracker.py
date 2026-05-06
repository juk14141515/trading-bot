"""Research-only near-miss tracker for Ponder Invest AI.

This module records scanner candidates that were close to useful thresholds but
were not necessarily traded. It never imports bot.py, never calls Alpaca, and
never changes live execution behavior.

Purpose:
- measure over-filtering without changing thresholds mid-day
- preserve rejected/near-threshold opportunities for later outcome analysis
- produce dashboard-ready JSON for the research UI
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA_DIR = ROOT / "research_data"
STATIC_RESEARCH_DIR = ROOT / "static" / "research"
NEAR_MISS_FILE = RESEARCH_DATA_DIR / "near_miss_signals.csv"
OUT_FILE = STATIC_RESEARCH_DIR / "near_miss_tracker_latest.json"
TOP_CANDIDATES = ROOT / "top_10_candidates_v2.json"
BOT_STATUS = ROOT / "bot_status.json"

FIELDS = [
    "near_miss_id",
    "timestamp",
    "symbol",
    "score",
    "entry_price",
    "market_regime",
    "source",
    "near_miss_type",
    "nearest_threshold",
    "threshold_gap",
    "score_band",
    "reason",
    "accepted_shadow_setup",
    "status",
]

# Research-only score landmarks. These do NOT change live logic.
THRESHOLDS = {
    "watch_floor": 63.0,
    "strong_watch": 75.0,
    "trade_ready": 80.0,
    "high_conviction": 90.0,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def ensure_file(path: Path = NEAR_MISS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def read_ids(path: Path = NEAR_MISS_FILE) -> set[str]:
    ensure_file(path)
    try:
        with path.open(newline="") as f:
            return {row.get("near_miss_id", "") for row in csv.DictReader(f) if row.get("near_miss_id")}
    except Exception:
        return set()


def make_near_miss_id(symbol: str, timestamp: str, source: str, near_miss_type: str) -> str:
    # Bucket by hour to prevent the same symbol spamming the file every scan cycle.
    bucket = str(timestamp or utc_now())[:13]
    raw = f"{source}|{symbol.upper()}|{near_miss_type}|{bucket}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def score_band(score: float) -> str:
    if score >= THRESHOLDS["high_conviction"]:
        return "90_plus_high_conviction"
    if score >= THRESHOLDS["trade_ready"]:
        return "80_89_trade_ready_near_high_conviction"
    if score >= THRESHOLDS["strong_watch"]:
        return "75_79_strong_watch_near_trade_ready"
    if score >= 68:
        return "68_74_watch_near_strong_watch"
    if score >= THRESHOLDS["watch_floor"]:
        return "63_67_watch_floor"
    return "below_watch_floor"


def classify_near_miss(candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a research-only near-miss classification for a candidate.

    This intentionally logs useful scanner candidates even if they are below
    future execution thresholds. It is not permission to trade.
    """
    score = safe_float(candidate.get("score"))
    if score < THRESHOLDS["watch_floor"]:
        return None

    if score < THRESHOLDS["strong_watch"]:
        nearest = THRESHOLDS["strong_watch"]
        kind = "near_strong_watch"
    elif score < THRESHOLDS["trade_ready"]:
        nearest = THRESHOLDS["trade_ready"]
        kind = "near_trade_ready"
    elif score < THRESHOLDS["high_conviction"]:
        nearest = THRESHOLDS["high_conviction"]
        kind = "near_high_conviction"
    else:
        nearest = THRESHOLDS["high_conviction"]
        kind = "high_conviction_seen"

    return {
        "near_miss_type": kind,
        "nearest_threshold": nearest,
        "threshold_gap": round(max(nearest - score, 0.0), 2),
        "score_band": score_band(score),
    }


def log_near_miss(
    candidate: Dict[str, Any],
    market_regime: str = "unknown",
    source: str = "daytime_top_candidates_shadow",
    timestamp: Optional[str] = None,
    path: Path = NEAR_MISS_FILE,
) -> bool:
    classification = classify_near_miss(candidate)
    if not classification:
        return False

    timestamp = timestamp or utc_now()
    symbol = str(candidate.get("symbol") or "").upper().strip()
    if not symbol or symbol == "-":
        return False

    ensure_file(path)
    near_miss_id = make_near_miss_id(symbol, timestamp, source, classification["near_miss_type"])
    if near_miss_id in read_ids(path):
        return False

    score = safe_float(candidate.get("score"))
    reason = str(candidate.get("reason") or candidate.get("trend") or "scanner candidate")[:300]
    row = {
        "near_miss_id": near_miss_id,
        "timestamp": timestamp,
        "symbol": symbol,
        "score": round(score, 2),
        "entry_price": candidate.get("entry_price", ""),
        "market_regime": str(market_regime or "unknown")[:80],
        "source": source,
        "near_miss_type": classification["near_miss_type"],
        "nearest_threshold": classification["nearest_threshold"],
        "threshold_gap": classification["threshold_gap"],
        "score_band": classification["score_band"],
        "reason": reason,
        "accepted_shadow_setup": "false",
        "status": "pending_outcome",
    }
    with path.open("a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)
    return True


def read_rows(path: Path = NEAR_MISS_FILE) -> List[Dict[str, Any]]:
    ensure_file(path)
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def build_latest_json(rows: List[Dict[str, Any]], candidates_seen: int = 0, logged_now: int = 0) -> Dict[str, Any]:
    STATIC_RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    recent = rows[-50:]
    by_band = Counter(row.get("score_band", "unknown") for row in rows)
    by_type = Counter(row.get("near_miss_type", "unknown") for row in rows)
    by_symbol = Counter(row.get("symbol", "") for row in rows if row.get("symbol"))

    top_recent = sorted(
        recent,
        key=lambda row: (safe_float(row.get("score")), -safe_float(row.get("threshold_gap"))),
        reverse=True,
    )[:15]

    repeated = [
        {"symbol": symbol, "count": count}
        for symbol, count in by_symbol.most_common(15)
        if count >= 2
    ]

    payload = {
        "status": "research_only",
        "mode": "near_miss_tracking",
        "generated_at": utc_now(),
        "updated_at": utc_now(),
        "summary": {
            "total_near_misses": len(rows),
            "candidates_seen_last_run": candidates_seen,
            "near_misses_logged_last_run": logged_now,
            "unique_symbols": len(by_symbol),
            "repeated_symbols_count": len(repeated),
        },
        "score_bands": dict(by_band),
        "near_miss_types": dict(by_type),
        "repeated_symbols": repeated,
        "top_recent_near_misses": top_recent,
        "explanation": [
            "Research-only tracker for candidates close to trade/quality thresholds.",
            "Use this to study over-filtering before changing live thresholds.",
            "This file does not affect live trading, orders, risk manager, or Alpaca behavior.",
        ],
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
        },
        "policy": {
            "watch_floor": THRESHOLDS["watch_floor"],
            "strong_watch": THRESHOLDS["strong_watch"],
            "trade_ready": THRESHOLDS["trade_ready"],
            "high_conviction": THRESHOLDS["high_conviction"],
            "dedupe_bucket": "source + symbol + near_miss_type + hour",
        },
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def log_near_misses_from_candidates(
    candidates: Iterable[Dict[str, Any]],
    market_regime: str = "unknown",
    source: str = "daytime_top_candidates_shadow",
) -> Dict[str, Any]:
    candidates_list = list(candidates or [])
    timestamp = utc_now()
    logged = 0
    for candidate in candidates_list:
        if log_near_miss(candidate, market_regime=market_regime, source=source, timestamp=timestamp):
            logged += 1

    rows = read_rows()
    payload = build_latest_json(rows, candidates_seen=len(candidates_list), logged_now=logged)
    return {
        "near_misses_logged": logged,
        "near_miss_total": payload["summary"]["total_near_misses"],
        "near_miss_json": str(OUT_FILE),
    }


def extract_candidates(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = []
        for key in ("candidates", "top_candidates", "scanner_top", "items", "rows", "data"):
            value = raw.get(key)
            if isinstance(value, list):
                rows = value
                break
    else:
        rows = []

    normalized: List[Dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol") or item.get("ticker") or item.get("asset")
        if not symbol:
            continue
        score = item.get("score") or item.get("final_score") or item.get("confidence") or item.get("total") or 0
        normalized.append({
            "symbol": str(symbol).upper(),
            "score": safe_float(score),
            "trend": item.get("trend") or item.get("market_trend") or item.get("label") or "unknown",
            "entry_price": item.get("entry_price") or item.get("price") or item.get("last_price") or "",
            "reason": item.get("reason") or item.get("summary") or item.get("thesis") or "top candidate artifact",
        })
    return normalized


def market_regime() -> str:
    status = read_json(BOT_STATUS, {})
    return str(
        status.get("market_trend")
        or status.get("trading_state")
        or status.get("why_not_trading")
        or "unknown"
    )[:80]


def main() -> Dict[str, Any]:
    candidates = extract_candidates(read_json(TOP_CANDIDATES, []))
    result = log_near_misses_from_candidates(
        candidates,
        market_regime=market_regime(),
        source="manual_near_miss_scan",
    )
    print(json.dumps({"status": "ok", **result}, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
