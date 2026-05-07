"""Live vs shadow confidence weighting engine.

Weights learning reliability using:
- live samples
- shadow confirmations
- evaluated outcomes
- stale feed penalties
- setup edge quality

Research-only. Never changes live trading.

Outputs:
- static/research/live_shadow_confidence_latest.json
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent
STATIC_RESEARCH = ROOT / "static" / "research"

SETUP_EDGE = STATIC_RESEARCH / "setup_edge_latest.json"
LEARNING_CONFIDENCE = STATIC_RESEARCH / "learning_confidence_latest.json"
SHADOW_COMPARISON = STATIC_RESEARCH / "shadow_live_comparison_latest.json"
THRESHOLD_PRESSURE = STATIC_RESEARCH / "threshold_pressure_latest.json"
EXIT_QUALITY = STATIC_RESEARCH / "exit_quality_latest.json"
OUT_FILE = STATIC_RESEARCH / "live_shadow_confidence_latest.json"


FRESHNESS_LIMITS = {
    "setup_edge": 360,
    "learning_confidence": 180,
    "shadow_comparison": 180,
    "threshold_pressure": 720,
    "exit_quality": 720,
}


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


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def file_age_minutes(path: Path) -> Optional[float]:
    try:
        if not path.exists():
            return None
        return round((time.time() - path.stat().st_mtime) / 60, 2)
    except Exception:
        return None


def freshness_penalty(age_minutes: Optional[float], limit: int) -> float:
    if age_minutes is None:
        return 15.0
    if age_minutes <= limit:
        return 0.0
    overflow = age_minutes - limit
    return min(25.0, round(overflow / 30, 2))


def confidence_label(score: float) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    return "LOW"


def main() -> Dict[str, Any]:
    started = time.time()

    setup_edge = read_json(SETUP_EDGE, {})
    learning_conf = read_json(LEARNING_CONFIDENCE, {})
    shadow_compare = read_json(SHADOW_COMPARISON, {})
    threshold_pressure = read_json(THRESHOLD_PRESSURE, {})
    exit_quality = read_json(EXIT_QUALITY, {})

    freshness = {
        "setup_edge": file_age_minutes(SETUP_EDGE),
        "learning_confidence": file_age_minutes(LEARNING_CONFIDENCE),
        "shadow_comparison": file_age_minutes(SHADOW_COMPARISON),
        "threshold_pressure": file_age_minutes(THRESHOLD_PRESSURE),
        "exit_quality": file_age_minutes(EXIT_QUALITY),
    }

    penalties = {
        name: freshness_penalty(age, FRESHNESS_LIMITS[name])
        for name, age in freshness.items()
    }

    setup_rows = setup_edge.get("all_setup_edges") or []
    strong_edges = len([r for r in setup_rows if r.get("edge") == "strong_positive_edge"])
    positive_edges = len([r for r in setup_rows if r.get("edge") in {"strong_positive_edge", "positive_edge"}])
    negative_edges = len([r for r in setup_rows if r.get("edge") == "negative_edge"])

    live_trades = safe_float(shadow_compare.get("live_trades"), 0) or 0
    evaluated_shadow = safe_float(shadow_compare.get("evaluated_shadow"), 0) or 0
    missed_winners = safe_float(shadow_compare.get("missed_winners"), 0) or 0
    bad_live_trades = safe_float(shadow_compare.get("bad_live_trades"), 0) or 0

    learning_score = safe_float(learning_conf.get("confidence_score"), 50) or 50
    threshold_conf = str((threshold_pressure.get("recommendation") or {}).get("confidence") or "LOW").upper()

    exit_summary = exit_quality.get("summary") or {}
    avg_hold_alpha = safe_float(exit_summary.get("avg_hold_alpha_pct"), 0) or 0

    confidence_score = 35.0
    confidence_score += min(25.0, positive_edges * 2.5)
    confidence_score += min(15.0, evaluated_shadow / 400)
    confidence_score += min(10.0, live_trades * 1.5)
    confidence_score += min(10.0, learning_score / 10)

    confidence_score -= min(20.0, negative_edges * 2)
    confidence_score -= min(15.0, bad_live_trades * 2)
    confidence_score -= min(10.0, missed_winners / 500)

    if avg_hold_alpha < -3:
        confidence_score -= 5
    elif avg_hold_alpha > 2:
        confidence_score += 3

    if threshold_conf == "LOW":
        confidence_score -= 4
    elif threshold_conf == "HIGH":
        confidence_score += 4

    total_penalty = sum(penalties.values())
    confidence_score -= total_penalty
    confidence_score = max(0.0, min(100.0, round(confidence_score, 2)))

    label = confidence_label(confidence_score)

    payload = {
        "status": "ok",
        "updated_at": utc_now(),
        "runtime_ms": int((time.time() - started) * 1000),
        "source": "live_shadow_confidence_weighter",
        "confidence_score": confidence_score,
        "confidence_label": label,
        "freshness": freshness,
        "freshness_penalties": penalties,
        "inputs": {
            "strong_positive_edges": strong_edges,
            "positive_edges": positive_edges,
            "negative_edges": negative_edges,
            "live_trades": live_trades,
            "evaluated_shadow": evaluated_shadow,
            "missed_winners": missed_winners,
            "bad_live_trades": bad_live_trades,
            "avg_hold_alpha_pct": avg_hold_alpha,
            "threshold_confidence": threshold_conf,
            "learning_confidence_score": learning_score,
        },
        "recommendation": {
            "status": "collect_more_data" if confidence_score < 75 else "research_quality_improving",
            "automation_allowed": False,
            "optimize_live_thresholds": False,
            "reason": (
                "Continue collecting live-shadow evidence before adaptive automation."
                if confidence_score < 75
                else "Research confidence is improving, but live automation remains disabled."
            ),
        },
        "safety": {
            "read_only": True,
            "automation_allowed": False,
            "live_trading_changed": False,
            "orders_enabled": False,
        },
        "notes": [
            "Freshness penalties prevent stale feeds from inflating confidence.",
            "Live evidence is weighted more heavily than historical-only evidence.",
            "This module is informational and does not change live trading behavior.",
        ],
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))

    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
