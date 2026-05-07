"""Setup outcome linker for Ponder Invest AI.

Connects setup identity events to available evaluation feeds.

Outputs:
- research_data/setup_outcome_links.csv
- static/research/setup_outcome_links_latest.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
STATIC_RESEARCH = ROOT / "static" / "research"

SETUP_IDENTITY_EVENTS = RESEARCH_DATA / "setup_identity_events.csv"
SHADOW_SETUPS = RESEARCH_DATA / "shadow_setups.csv"
NEAR_MISS_OUTCOMES = RESEARCH_DATA / "near_miss_outcomes.csv"
EXIT_QUALITY = RESEARCH_DATA / "exit_quality_evaluations.csv"

OUT_CSV = RESEARCH_DATA / "setup_outcome_links.csv"
OUT_JSON = STATIC_RESEARCH / "setup_outcome_links_latest.json"

FIELDS = [
    "link_id", "timestamp", "symbol", "setup_type", "setup_family",
    "event_type", "source", "score", "outcome_status", "return_30m_pct",
    "return_60m_pct", "return_1d_pct", "return_3d_pct", "return_5d_pct",
    "max_return_pct", "best_window", "became_winner", "exit_quality_score",
    "hold_alpha_pct", "matched_sources", "confidence", "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, "", "None", "nan", "NaN"):
            return default
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def safe_round(value: Any, digits: int = 4) -> Any:
    value = safe_float(value)
    return "" if value is None else round(value, digits)


def read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def parse_dt(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def family_for(setup_type: str) -> str:
    setup_type = str(setup_type or "unknown")
    for key in ("crypto", "ipo", "gap", "pullback", "breakout", "momentum"):
        if key in setup_type:
            return key
    if "earnings" in setup_type or "news" in setup_type:
        return "catalyst"
    if "near_" in setup_type:
        return "near_miss"
    return "general"


def make_link_id(row: Dict[str, Any]) -> str:
    raw = "|".join(str(row.get(k) or "") for k in ("timestamp", "symbol", "setup_type", "event_type", "source"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def minutes_apart(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
    if not a or not b:
        return None
    return abs((a - b).total_seconds()) / 60.0


def by_symbol(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        symbol = normalize_symbol(row.get("symbol"))
        if symbol:
            out[symbol].append(row)
    return out


def nearest(event: Dict[str, Any], rows: List[Dict[str, Any]], max_minutes: int) -> Optional[Dict[str, Any]]:
    event_dt = parse_dt(event.get("timestamp"))
    best = None
    best_distance = None
    for row in rows:
        row_dt = parse_dt(row.get("timestamp") or row.get("time") or row.get("date"))
        distance = minutes_apart(event_dt, row_dt)
        if distance is None or distance > max_minutes:
            continue
        if best_distance is None or distance < best_distance:
            best = row
            best_distance = distance
    return best


def winner_flag(row: Dict[str, Any]) -> str:
    value = str(row.get("became_winner") or "").strip().lower()
    if value in {"true", "1", "yes"}:
        return "true"
    if value in {"false", "0", "no"}:
        return "false"
    max_return = safe_float(row.get("max_future_return") or row.get("max_return_pct"))
    if max_return is None:
        return ""
    return "true" if max_return >= 3 else "false"


def link_event(event: Dict[str, Any], near_map: Dict[str, List[Dict[str, Any]]], shadow_map: Dict[str, List[Dict[str, Any]]], exit_map: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    symbol = normalize_symbol(event.get("symbol"))
    setup_type = event.get("setup_type") or "unknown"
    matched: List[str] = []
    notes: List[str] = []

    near = nearest(event, near_map.get(symbol, []), 4320)
    shadow = nearest(event, shadow_map.get(symbol, []), 4320)
    exit_row = nearest(event, exit_map.get(symbol, []), 4320)

    if near:
        matched.append("near_miss_outcomes")
    if shadow:
        matched.append("shadow_setups")
    if exit_row:
        matched.append("exit_quality")

    returns = {
        "30m": safe_float((near or {}).get("future_return_30m") or (near or {}).get("return_30m_pct")),
        "60m": safe_float((near or {}).get("future_return_60m") or (near or {}).get("return_60m_pct")),
        "1d": safe_float((near or {}).get("future_return_1d") or (near or {}).get("return_1d_pct")),
        "3d": safe_float((near or {}).get("future_return_3d") or (near or {}).get("return_3d_pct")),
        "5d": safe_float((near or {}).get("future_return_5d") or (near or {}).get("return_5d_pct")),
    }
    max_return = safe_float((near or {}).get("max_future_return") or (near or {}).get("max_return_pct"))
    if max_return is None:
        valid_returns = [v for v in returns.values() if v is not None]
        max_return = max(valid_returns) if valid_returns else None

    status = "linked" if matched else "unlinked_pending"
    if near and str(near.get("status") or "").lower() in {"pending", "pending_maturity", "future_timestamp_pending"}:
        status = "pending_maturity"
        notes.append("near-miss outcome not mature yet")
    elif not matched:
        notes.append("no evaluation row matched yet")

    exit_score = safe_float((exit_row or {}).get("exit_quality_score") or (exit_row or {}).get("score"))
    hold_alpha = safe_float((exit_row or {}).get("hold_alpha_pct"))

    confidence = "LOW"
    if near or exit_row:
        confidence = "MEDIUM"
    if near and exit_row and (returns["1d"] is not None or returns["5d"] is not None):
        confidence = "HIGH"

    linked = {
        "timestamp": event.get("timestamp") or utc_now(),
        "symbol": symbol,
        "setup_type": setup_type,
        "setup_family": event.get("setup_family") or family_for(setup_type),
        "event_type": event.get("event_type") or "unknown",
        "source": event.get("source") or "setup_identity_events",
        "score": safe_round(event.get("score"), 2),
        "outcome_status": status,
        "return_30m_pct": safe_round(returns["30m"]),
        "return_60m_pct": safe_round(returns["60m"]),
        "return_1d_pct": safe_round(returns["1d"]),
        "return_3d_pct": safe_round(returns["3d"]),
        "return_5d_pct": safe_round(returns["5d"]),
        "max_return_pct": safe_round(max_return),
        "best_window": (near or {}).get("best_window") or "",
        "became_winner": winner_flag(near or {}),
        "exit_quality_score": safe_round(exit_score, 2),
        "hold_alpha_pct": safe_round(hold_alpha),
        "matched_sources": ",".join(matched),
        "confidence": confidence,
        "notes": "; ".join(notes),
    }
    linked["link_id"] = make_link_id(linked)
    return linked


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("setup_type") or "unknown"].append(row)

    setup_summary = []
    for setup_type, items in grouped.items():
        linked = [r for r in items if r.get("outcome_status") == "linked"]
        winners = [r for r in linked if str(r.get("became_winner")).lower() == "true"]
        max_returns = [safe_float(r.get("max_return_pct")) for r in linked]
        max_returns = [x for x in max_returns if x is not None]
        exit_scores = [safe_float(r.get("exit_quality_score")) for r in linked]
        exit_scores = [x for x in exit_scores if x is not None]
        setup_summary.append({
            "setup_type": setup_type,
            "samples": len(items),
            "linked": len(linked),
            "pending": len(items) - len(linked),
            "winner_count": len(winners),
            "winner_rate": round((len(winners) / max(1, len(linked))) * 100, 2),
            "avg_max_return_pct": round(mean(max_returns), 4) if max_returns else None,
            "avg_exit_quality_score": round(mean(exit_scores), 2) if exit_scores else None,
            "confidence": "HIGH" if len(linked) >= 30 else "MEDIUM" if len(linked) >= 10 else "LOW",
        })
    setup_summary.sort(key=lambda r: ((r["avg_max_return_pct"] if r["avg_max_return_pct"] is not None else -999), r["linked"]), reverse=True)
    return {
        "setup_summary": setup_summary,
        "status_counts": dict(Counter(r.get("outcome_status") or "unknown" for r in rows)),
        "confidence_counts": dict(Counter(r.get("confidence") or "LOW" for r in rows)),
    }


def main() -> Dict[str, Any]:
    started = time.time()
    events = read_csv(SETUP_IDENTITY_EVENTS)
    near_map = by_symbol(read_csv(NEAR_MISS_OUTCOMES))
    shadow_map = by_symbol(read_csv(SHADOW_SETUPS))
    exit_map = by_symbol(read_csv(EXIT_QUALITY))

    rows = [link_event(event, near_map, shadow_map, exit_map) for event in events]
    write_csv(OUT_CSV, rows)
    summary = summarize(rows)
    linked_count = sum(1 for row in rows if row.get("outcome_status") == "linked")

    payload = {
        "status": "ok",
        "mode": "setup_outcome_linking",
        "updated_at": utc_now(),
        "runtime_ms": int((time.time() - started) * 1000),
        "records": len(rows),
        "source": "setup_outcome_linker_v1",
        "outputs": {
            "links_csv": str(OUT_CSV.relative_to(ROOT)),
            "latest_json": str(OUT_JSON.relative_to(ROOT)),
        },
        "summary": {
            "linked_count": linked_count,
            "pending_count": len(rows) - linked_count,
            "link_rate": round((linked_count / max(1, len(rows))) * 100, 2),
            **summary,
        },
        "top_setup_summaries": summary["setup_summary"][:10],
        "guardrails": {
            "read_only": True,
            "automation_allowed": False,
        },
        "notes": [
            "Links setup identities to evaluation feeds when available.",
            "Pending rows are normal while outcome windows mature.",
            "This module is informational only.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
