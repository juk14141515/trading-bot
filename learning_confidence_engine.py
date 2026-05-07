"""Research-only learning confidence engine for Ponder Invest AI.

Produces a system-wide learning confidence gate so adaptive logic can know
whether the current research data is trustworthy enough for future changes.

Safety guarantees:
- never imports bot.py
- never calls Alpaca or order APIs
- never places trades
- never changes thresholds, sizing, or execution behavior
- writes dashboard/research JSON only
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
STATIC_RESEARCH = ROOT / "static" / "research"
OUT_FILE = STATIC_RESEARCH / "learning_confidence_latest.json"

FILES = {
    "near_miss_outcomes": STATIC_RESEARCH / "near_miss_outcomes_latest.json",
    "threshold_pressure": STATIC_RESEARCH / "threshold_pressure_latest.json",
    "shadow_live_comparison": STATIC_RESEARCH / "shadow_live_comparison_latest.json",
    "shadow_execution": STATIC_RESEARCH / "shadow_execution_latest.json",
    "shadow_capital_allocator": STATIC_RESEARCH / "shadow_capital_allocator_v2_latest.json",
    "research_scheduler": STATIC_RESEARCH / "research_scheduler_latest.json",
    "system_snapshot": STATIC_RESEARCH / "system_snapshot_latest.json",
    "market_regime": STATIC_RESEARCH / "market_regime_filter_latest.json",
    "rotation_engine": STATIC_RESEARCH / "rotation_engine_latest.json",
    "sell_intelligence": STATIC_RESEARCH / "sell_intelligence_latest.json",
    "capital_intelligence": STATIC_RESEARCH / "capital_intelligence_latest.json",
}

# Freshness expectations are intentionally loose because some feeds are expected
# to update after close/overnight rather than every few minutes.
FRESHNESS_LIMITS_MINUTES = {
    "near_miss_outcomes": 360,
    "threshold_pressure": 360,
    "shadow_live_comparison": 240,
    "shadow_execution": 240,
    "shadow_capital_allocator": 240,
    "research_scheduler": 240,
    "system_snapshot": 360,
    "market_regime": 720,
    "rotation_engine": 720,
    "sell_intelligence": 720,
    "capital_intelligence": 720,
}


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


def utc_now() -> str:
    return utc_now_dt().isoformat(timespec="seconds")


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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def score_sample_depth(near_miss: Dict[str, Any], comparison: Dict[str, Any]) -> Dict[str, Any]:
    nm_summary = near_miss.get("summary", {}) if isinstance(near_miss, dict) else {}
    comp_summary = comparison.get("summary", {}) if isinstance(comparison, dict) else {}

    mature_near_miss = safe_int(near_miss.get("mature_records") or nm_summary.get("evaluated_count"))
    pending_near_miss = safe_int(near_miss.get("pending_records") or nm_summary.get("pending_count"))
    evaluated_live_shadow = safe_int(comp_summary.get("evaluated_live_shadow_opportunities_count"))
    live_trades = safe_int(comp_summary.get("live_trades_count"))

    score = 0
    reasons: List[str] = []

    if mature_near_miss >= 100:
        score += 30
        reasons.append("Near-miss mature sample is strong.")
    elif mature_near_miss >= 30:
        score += 20
        reasons.append("Near-miss mature sample is usable but still early.")
    elif mature_near_miss >= 10:
        score += 10
        reasons.append("Near-miss mature sample is beginning to form.")
    else:
        reasons.append("Near-miss mature sample is too small for tuning.")

    if evaluated_live_shadow >= 300:
        score += 30
        reasons.append("Live-shadow evaluated sample is strong.")
    elif evaluated_live_shadow >= 100:
        score += 20
        reasons.append("Live-shadow evaluated sample is usable.")
    elif evaluated_live_shadow >= 25:
        score += 10
        reasons.append("Live-shadow evaluated sample is early.")
    else:
        reasons.append("Live-shadow evaluated sample is too small.")

    if live_trades >= 30:
        score += 15
        reasons.append("Live trade sample is beginning to support execution conclusions.")
    elif live_trades >= 10:
        score += 8
        reasons.append("Live trade sample exists but is still thin.")
    else:
        reasons.append("Live trade sample is too small for live logic changes.")

    if pending_near_miss > mature_near_miss * 3 and mature_near_miss < 30:
        score -= 5
        reasons.append("Most near-miss rows are still pending maturity.")

    return {
        "score": max(0, min(score, 75)),
        "mature_near_miss": mature_near_miss,
        "pending_near_miss": pending_near_miss,
        "evaluated_live_shadow": evaluated_live_shadow,
        "live_trades": live_trades,
        "reasons": reasons,
    }


def score_freshness() -> Dict[str, Any]:
    score = 0
    stale = []
    missing = []
    fresh = []
    details = {}

    for name, path in FILES.items():
        age = file_age_minutes(path)
        limit = FRESHNESS_LIMITS_MINUTES.get(name, 360)
        exists = path.exists()
        status = "fresh"
        if not exists:
            status = "missing"
            missing.append(name)
        elif age is None:
            status = "unknown"
            stale.append(name)
        elif age > limit:
            status = "stale"
            stale.append(name)
        else:
            fresh.append(name)

        details[name] = {
            "exists": exists,
            "age_minutes": age,
            "limit_minutes": limit,
            "status": status,
            "path": str(path.relative_to(ROOT)),
        }

    total = len(FILES)
    fresh_ratio = len(fresh) / max(total, 1)
    score = round(fresh_ratio * 25)

    return {
        "score": score,
        "fresh_count": len(fresh),
        "stale_count": len(stale),
        "missing_count": len(missing),
        "fresh": fresh,
        "stale": stale,
        "missing": missing,
        "details": details,
    }


def score_threshold_safety(threshold_pressure: Dict[str, Any]) -> Dict[str, Any]:
    recommendation = threshold_pressure.get("recommendation", {}) if isinstance(threshold_pressure, dict) else {}
    mature_records = safe_int(threshold_pressure.get("mature_records")) if isinstance(threshold_pressure, dict) else 0
    action = recommendation.get("action", "unknown") if isinstance(recommendation, dict) else "unknown"
    automation_allowed = bool(recommendation.get("automation_allowed", False)) if isinstance(recommendation, dict) else False

    score = 0
    reasons = []

    if mature_records >= 100:
        score += 15
        reasons.append("Threshold pressure has strong mature sample depth.")
    elif mature_records >= 30:
        score += 10
        reasons.append("Threshold pressure has medium mature sample depth.")
    elif mature_records >= 10:
        score += 5
        reasons.append("Threshold pressure has early mature sample depth.")
    else:
        reasons.append("Threshold pressure sample is too small.")

    if action in {"collect_more_data", "hold_thresholds"}:
        score += 5
        reasons.append("Recommendation is conservative.")
    elif action == "research_only_watch_lower_threshold":
        score += 3
        reasons.append("Potential threshold change is research-only and not automated.")

    if not automation_allowed:
        score += 5
        reasons.append("Automation is disabled for threshold changes.")
    else:
        reasons.append("WARNING: automation_allowed is true; this should remain false.")
        score -= 10

    return {
        "score": max(0, min(score, 25)),
        "mature_records": mature_records,
        "action": action,
        "automation_allowed": automation_allowed,
        "reasons": reasons,
    }


def confidence_label(total_score: int) -> str:
    if total_score >= 75:
        return "HIGH"
    if total_score >= 50:
        return "MEDIUM"
    return "LOW"


def decide_allowed_actions(label: str, sample_depth: Dict[str, Any], freshness: Dict[str, Any]) -> Dict[str, Any]:
    mature = sample_depth.get("mature_near_miss", 0)
    evaluated_live_shadow = sample_depth.get("evaluated_live_shadow", 0)
    stale_count = freshness.get("stale_count", 0)
    missing_count = freshness.get("missing_count", 0)

    return {
        "observe_only": True,
        "allow_dashboard_display": True,
        "allow_research_recommendations": label in {"MEDIUM", "HIGH"},
        "allow_shadow_threshold_tests": mature >= 30 and stale_count <= 3,
        "allow_live_threshold_change": False,
        "allow_live_reentry_change": False,
        "allow_live_allocator_change": False,
        "allow_real_money_scaling": False,
        "reason": (
            "Live changes remain disabled. Require higher sample depth, fewer stale feeds, "
            "and manual review before any live behavior changes."
        ),
        "requirements_for_next_level": {
            "mature_near_miss_minimum": 30 if mature < 30 else 100,
            "evaluated_live_shadow_minimum": 100 if evaluated_live_shadow < 100 else 300,
            "max_stale_feeds": 3,
            "max_missing_feeds": 2,
            "current_mature_near_miss": mature,
            "current_evaluated_live_shadow": evaluated_live_shadow,
            "current_stale_feeds": stale_count,
            "current_missing_feeds": missing_count,
        },
    }


def build_learning_confidence() -> Dict[str, Any]:
    started = time.time()
    STATIC_RESEARCH.mkdir(parents=True, exist_ok=True)

    near_miss = read_json(FILES["near_miss_outcomes"], {})
    threshold_pressure = read_json(FILES["threshold_pressure"], {})
    comparison = read_json(FILES["shadow_live_comparison"], {})

    sample_depth = score_sample_depth(near_miss, comparison)
    freshness = score_freshness()
    threshold_safety = score_threshold_safety(threshold_pressure)

    total_score = max(0, min(100, sample_depth["score"] + freshness["score"] + threshold_safety["score"]))
    label = confidence_label(total_score)
    allowed_actions = decide_allowed_actions(label, sample_depth, freshness)

    blockers = []
    if sample_depth["mature_near_miss"] < 30:
        blockers.append("Need at least 30 mature near-miss outcomes before threshold tuning.")
    if sample_depth["evaluated_live_shadow"] < 100:
        blockers.append("Need at least 100 evaluated live-shadow opportunities before stronger adaptive conclusions.")
    if freshness["stale_count"] > 3:
        blockers.append("Too many stale research feeds. Validate scheduler/freshness before trusting learning outputs.")
    if freshness["missing_count"] > 2:
        blockers.append("Too many missing research feeds. Dashboard/backend integration is incomplete.")

    payload = {
        "status": "ok",
        "version": "learning_confidence_engine_v1",
        "updated_at": utc_now(),
        "runtime_ms": int((time.time() - started) * 1000),
        "source": "learning_confidence_engine",
        "learning_confidence": label,
        "learning_score": total_score,
        "components": {
            "sample_depth": sample_depth,
            "freshness": freshness,
            "threshold_safety": threshold_safety,
        },
        "blockers": blockers,
        "allowed_actions": allowed_actions,
        "recommendation": {
            "mode": "observe_only" if label == "LOW" else "research_recommendations_only",
            "summary": (
                "Keep collecting data; do not change live trading logic yet."
                if label == "LOW"
                else "Research-only recommendations may be reviewed, but live trading changes remain disabled."
            ),
        },
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
            "live_threshold_change_allowed": False,
            "live_reentry_change_allowed": False,
            "live_allocator_change_allowed": False,
        },
        "notes": [
            "This engine is a trust gate for future adaptive logic.",
            "LOW confidence means observe only and continue collecting live-shadow data.",
            "MEDIUM confidence can support research-only recommendations.",
            "HIGH confidence is still not permission to auto-change live trading without manual review.",
        ],
    }

    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> Dict[str, Any]:
    payload = build_learning_confidence()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
