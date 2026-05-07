"""Setup edge evaluator for Ponder Invest AI.

Aggregates evaluated setup outcomes into a research-only edge table.
This module intentionally does NOT change live thresholds or execution.

Outputs:
- static/research/setup_edge_latest.json
"""

from __future__ import annotations

import csv
import json
import math
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
STATIC_RESEARCH = ROOT / "static" / "research"

SETUP_EVENTS = RESEARCH_DATA / "setup_identity_events.csv"
SETUP_OUTCOMES = STATIC_RESEARCH / "setup_outcomes_latest.json"
NEAR_MISS_OUTCOMES = RESEARCH_DATA / "near_miss_outcomes.csv"
EXIT_QUALITY = RESEARCH_DATA / "exit_quality_evaluations.csv"
OUT_FILE = STATIC_RESEARCH / "setup_edge_latest.json"


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


def classify_edge(avg_return_5d: float, win_rate: float, samples: int) -> str:
    if samples < 10:
        return "insufficient_samples"
    if avg_return_5d >= 5 and win_rate >= 55:
        return "strong_positive_edge"
    if avg_return_5d >= 2 and win_rate >= 50:
        return "positive_edge"
    if avg_return_5d <= -2:
        return "negative_edge"
    return "mixed_edge"


def confidence_label(samples: int, live_samples: int) -> str:
    if live_samples >= 25 and samples >= 100:
        return "HIGH"
    if live_samples >= 10 and samples >= 40:
        return "MEDIUM"
    return "LOW"


def main() -> Dict[str, Any]:
    started = time.time()

    setup_events = read_csv(SETUP_EVENTS)
    near_miss_rows = read_csv(NEAR_MISS_OUTCOMES)
    exit_rows = read_csv(EXIT_QUALITY)
    setup_outcomes = read_json(SETUP_OUTCOMES, {})

    grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "setup_type": "unknown",
        "samples": 0,
        "live_samples": 0,
        "shadow_samples": 0,
        "near_miss_samples": 0,
        "returns_1d": [],
        "returns_5d": [],
        "scores": [],
        "winners": 0,
        "losers": 0,
        "hold_alpha": [],
        "source_breakdown": defaultdict(int),
    })

    for row in setup_events:
        setup_type = row.get("setup_type") or "unknown"
        bucket = grouped[setup_type]
        bucket["setup_type"] = setup_type
        bucket["samples"] += 1
        bucket["source_breakdown"][row.get("source") or "unknown"] += 1

        score = safe_float(row.get("score"))
        if score is not None:
            bucket["scores"].append(score)

        event_type = row.get("event_type") or ""
        if event_type == "live_trade":
            bucket["live_samples"] += 1
        elif event_type == "shadow_setup":
            bucket["shadow_samples"] += 1
        elif event_type == "near_miss":
            bucket["near_miss_samples"] += 1

    for row in near_miss_rows:
        setup_type = row.get("setup_type") or "unknown"
        bucket = grouped[setup_type]

        r1 = safe_float(row.get("return_1d_pct"))
        r5 = safe_float(row.get("return_5d_pct"))

        if r1 is not None:
            bucket["returns_1d"].append(r1)
        if r5 is not None:
            bucket["returns_5d"].append(r5)
            if r5 > 0:
                bucket["winners"] += 1
            else:
                bucket["losers"] += 1

    for row in exit_rows:
        setup_type = row.get("setup_type") or "unknown"
        bucket = grouped[setup_type]
        hold_alpha = safe_float(row.get("hold_alpha_pct"))
        if hold_alpha is not None:
            bucket["hold_alpha"].append(hold_alpha)

    setup_perf = setup_outcomes.get("setup_performance") or {}

    output_rows = []
    for setup_type, data in grouped.items():
        perf = setup_perf.get(setup_type, {}) if isinstance(setup_perf, dict) else {}

        avg_1d = mean(data["returns_1d"]) if data["returns_1d"] else safe_float(perf.get("avg_1d_return"), 0.0) or 0.0
        avg_5d = mean(data["returns_5d"]) if data["returns_5d"] else safe_float(perf.get("avg_5d_return"), 0.0) or 0.0
        avg_score = mean(data["scores"]) if data["scores"] else safe_float(perf.get("avg_score"), 0.0) or 0.0
        hold_alpha = mean(data["hold_alpha"]) if data["hold_alpha"] else 0.0

        wins = data["winners"]
        losses = data["losers"]
        total_eval = wins + losses
        win_rate = round((wins / max(1, total_eval)) * 100, 2)

        edge = classify_edge(avg_5d, win_rate, data["samples"])
        confidence = confidence_label(data["samples"], data["live_samples"])

        output_rows.append({
            "setup_type": setup_type,
            "samples": data["samples"],
            "live_samples": data["live_samples"],
            "shadow_samples": data["shadow_samples"],
            "near_miss_samples": data["near_miss_samples"],
            "avg_score": round(avg_score, 3),
            "avg_1d_return": round(avg_1d, 3),
            "avg_5d_return": round(avg_5d, 3),
            "win_rate": win_rate,
            "hold_alpha_pct": round(hold_alpha, 3),
            "edge": edge,
            "confidence": confidence,
            "source_breakdown": dict(data["source_breakdown"]),
        })

    output_rows.sort(key=lambda r: (r["avg_5d_return"], r["win_rate"]), reverse=True)

    payload = {
        "status": "ok",
        "updated_at": utc_now(),
        "runtime_ms": int((time.time() - started) * 1000),
        "records": len(output_rows),
        "source": "setup_edge_evaluator_v1",
        "safety": {
            "read_only": True,
            "automation_allowed": False,
            "live_trading_changed": False,
        },
        "summary": {
            "positive_edge_setups": len([r for r in output_rows if r["edge"] in {"positive_edge", "strong_positive_edge"}]),
            "negative_edge_setups": len([r for r in output_rows if r["edge"] == "negative_edge"]),
            "insufficient_sample_setups": len([r for r in output_rows if r["edge"] == "insufficient_samples"]),
        },
        "top_positive_edges": output_rows[:10],
        "worst_edges": sorted(output_rows, key=lambda r: r["avg_5d_return"])[:10],
        "all_setup_edges": output_rows,
        "notes": [
            "This evaluator aggregates setup behavior into research-only edge rankings.",
            "Historical/backfill data should not override live-shadow evidence.",
            "No thresholds or live execution rules are modified here.",
        ],
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))

    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
