"""Setup identity engine for Ponder Invest AI.

Creates a consistent setup_type label for live trades, shadow rows, near-miss rows,
and scanner candidates. This is a research/data-quality layer only.

Outputs:
- research_data/setup_identity_events.csv
- static/research/setup_identity_latest.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
STATIC_RESEARCH = ROOT / "static" / "research"

OUT_CSV = RESEARCH_DATA / "setup_identity_events.csv"
OUT_JSON = STATIC_RESEARCH / "setup_identity_latest.json"

SOURCES = {
    "trade_history": ROOT / "trade_history.csv",
    "shadow_setups": RESEARCH_DATA / "shadow_setups.csv",
    "near_miss_signals": RESEARCH_DATA / "near_miss_signals.csv",
    "top_candidates": ROOT / "top_10_candidates_v2.json",
}

FIELDS = [
    "event_id",
    "timestamp",
    "symbol",
    "event_type",
    "setup_type",
    "setup_family",
    "source",
    "score",
    "confidence",
    "reason",
    "raw_label",
    "raw_source",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, "", "None", "nan", "NaN"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def text_blob(row: Dict[str, Any]) -> str:
    return " ".join(str(v or "") for v in row.values()).lower()


def existing_setup(row: Dict[str, Any]) -> str:
    for key in ("setup_type", "setup", "strategy", "signal_type", "near_miss_type"):
        value = str(row.get(key) or "").strip().lower()
        if value and value not in {"unknown", "none", "nan", "general"}:
            return value
    return ""


def setup_family(setup_type: str) -> str:
    if "crypto" in setup_type:
        return "crypto"
    if "ipo" in setup_type:
        return "ipo"
    if "earnings" in setup_type or "news" in setup_type:
        return "catalyst"
    if "day_trade" in setup_type or "momentum" in setup_type:
        return "momentum"
    if "gap" in setup_type:
        return "gap"
    if "pullback" in setup_type:
        return "pullback"
    if "breakout" in setup_type:
        return "breakout"
    if "etf" in setup_type:
        return "etf"
    return "general"


def classify_setup(row: Dict[str, Any]) -> tuple[str, str, str]:
    """Return setup_type, confidence, reason."""
    current = existing_setup(row)
    if current:
        return current, "high", "existing setup_type present"

    symbol = normalize_symbol(row.get("symbol") or row.get("ticker") or row.get("asset"))
    blob = text_blob(row)

    score = safe_float(row.get("score") or row.get("final_score") or row.get("entry_score"))
    momentum = safe_float(row.get("momentum_score"))
    trend = safe_float(row.get("trend_score"))
    volume_ratio = safe_float(row.get("volume_ratio"))
    change_1d = safe_float(row.get("change_1d_pct"))
    change_5d = safe_float(row.get("change_5d_pct"))
    extension = safe_float(row.get("extension_from_sma20_pct"))

    if symbol.endswith("-USD") or "crypto" in blob:
        return "crypto_momentum", "medium", "crypto symbol/text detected"
    if "ipo" in blob or "recent ipo" in blob:
        return "ipo_recent", "medium", "IPO/recent listing text detected"
    if "earnings" in blob or "catalyst" in blob or "news" in blob:
        return "earnings_reaction", "medium", "earnings/news/catalyst text detected"
    if change_1d is not None and change_1d >= 3 and (volume_ratio or 0) >= 1.2:
        return "gap_up_gap_down", "medium", "large 1-day move with elevated volume"
    if extension is not None and extension >= 15 and (score or 0) >= 70:
        return "gap_up_gap_down", "medium", "extended from SMA20 with strong score"
    if (momentum or 0) >= 90 and (score or 0) >= 80:
        return "day_trade_momentum", "medium", "high momentum/high score candidate"
    if (trend or 0) >= 80 and 65 <= (score or 0) < 80:
        return "large_cap_pullback", "low", "high trend with mid score"
    if (change_5d or 0) >= 8 and (score or 0) >= 70:
        return "small_cap_breakout", "low", "strong 5-day move with acceptable score"
    if symbol in {"SPY", "QQQ", "IWM", "DIA", "VTI", "VOO"}:
        return "etf_trend", "medium", "ETF symbol detected"
    if score is not None and score >= 63:
        return "general_momentum", "low", "scored candidate without stronger setup identity"
    return "unknown", "low", "not enough fields to classify confidently"


def make_event_id(source: str, row: Dict[str, Any], setup_type: str) -> str:
    raw = "|".join([
        source,
        str(row.get("timestamp") or row.get("time") or row.get("date") or ""),
        normalize_symbol(row.get("symbol") or row.get("ticker") or row.get("asset")),
        setup_type,
        str(row.get("score") or row.get("final_score") or ""),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_event(source: str, row: Dict[str, Any], event_type: str) -> Dict[str, Any]:
    setup_type, confidence, reason = classify_setup(row)
    symbol = normalize_symbol(row.get("symbol") or row.get("ticker") or row.get("asset"))
    score = safe_float(row.get("score") or row.get("final_score") or row.get("entry_score"))
    timestamp = str(row.get("timestamp") or row.get("time") or row.get("date") or utc_now())
    return {
        "event_id": make_event_id(source, row, setup_type),
        "timestamp": timestamp,
        "symbol": symbol,
        "event_type": event_type,
        "setup_type": setup_type,
        "setup_family": setup_family(setup_type),
        "source": source,
        "score": round(score, 2) if score is not None else "",
        "confidence": confidence,
        "reason": reason,
        "raw_label": row.get("label") or row.get("entry_zone") or row.get("status") or "",
        "raw_source": row.get("source") or source,
    }


def load_events() -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    for row in read_csv(SOURCES["trade_history"]):
        if normalize_symbol(row.get("symbol") or row.get("ticker")):
            events.append(normalize_event("trade_history", row, "live_trade"))

    for row in read_csv(SOURCES["shadow_setups"]):
        events.append(normalize_event("shadow_setups", row, "shadow_setup"))

    for row in read_csv(SOURCES["near_miss_signals"]):
        events.append(normalize_event("near_miss_signals", row, "near_miss"))

    raw_candidates = read_json(SOURCES["top_candidates"], [])
    if isinstance(raw_candidates, dict):
        candidates = (
            raw_candidates.get("candidates")
            or raw_candidates.get("top_10")
            or raw_candidates.get("results")
            or []
        )
    else:
        candidates = raw_candidates
    if isinstance(candidates, list):
        for row in candidates:
            if isinstance(row, dict):
                events.append(normalize_event("top_candidates", row, "scanner_candidate"))

    seen = set()
    deduped = []
    for event in events:
        if event["event_id"] in seen:
            continue
        seen.add(event["event_id"])
        deduped.append(event)
    return deduped


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def main() -> Dict[str, Any]:
    started = time.time()
    events = load_events()
    write_csv(OUT_CSV, events)

    by_setup = Counter(e["setup_type"] for e in events)
    by_event_type = Counter(e["event_type"] for e in events)
    by_confidence = Counter(e["confidence"] for e in events)

    unknown_count = by_setup.get("unknown", 0)
    payload = {
        "status": "ok",
        "mode": "setup_identity_research",
        "updated_at": utc_now(),
        "runtime_ms": int((time.time() - started) * 1000),
        "records": len(events),
        "source": "setup_identity_engine",
        "outputs": {
            "events_csv": str(OUT_CSV.relative_to(ROOT)),
            "latest_json": str(OUT_JSON.relative_to(ROOT)),
        },
        "safety": {
            "read_only": True,
            "automation_allowed": False,
            "live_trading_changed": False,
        },
        "summary": {
            "identified_count": len(events) - unknown_count,
            "unknown_count": unknown_count,
            "unknown_rate": round((unknown_count / max(1, len(events))) * 100, 2),
            "by_event_type": dict(by_event_type),
            "by_confidence": dict(by_confidence),
        },
        "top_setup_types": [
            {"setup_type": k, "count": v, "family": setup_family(k)}
            for k, v in by_setup.most_common(20)
        ],
        "notes": [
            "This file standardizes setup identity for later learning modules.",
            "Unknown setup types should shrink over time as live entries/skips carry richer context.",
            "This output is informational and does not change live behavior.",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
