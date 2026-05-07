"""Research-only near miss outcome evaluator for Ponder Invest AI.

Evaluates whether near-miss/rejected candidates later became strong performers.
This module NEVER modifies live trading logic, Alpaca execution, thresholds,
or bot.py behavior.

v1.1 adds outcome maturity gates so too-new/future rows are marked pending
instead of being counted as failed near-misses.
v1.2 adds threshold pressure intelligence: safe recommendation-only diagnostics
for small threshold changes using mature rows only.
"""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yfinance as yf

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
STATIC_RESEARCH = ROOT / "static" / "research"

INPUT_CSV = RESEARCH_DATA / "near_miss_signals.csv"
OUTCOME_CSV = RESEARCH_DATA / "near_miss_outcomes.csv"
OUTCOME_JSON = STATIC_RESEARCH / "near_miss_outcomes_latest.json"
THRESHOLD_JSON = STATIC_RESEARCH / "threshold_pressure_latest.json"

WINDOWS = {
    "30m": 30,
    "60m": 60,
    "1d": 1440,
    "3d": 4320,
    "5d": 7200,
}

THRESHOLDS = [70, 72, 75, 78, 80]
BASELINE_THRESHOLD = 80
WINNER_THRESHOLD = 3.0
BAD_SIGNAL_THRESHOLD = -1.0
MIN_EVALUATED_FOR_MEDIUM = 30
MIN_EVALUATED_FOR_HIGH = 100

FIELDS = [
    "symbol",
    "timestamp",
    "score",
    "nearest_threshold",
    "near_miss_type",
    "reason",
    "future_return_30m",
    "future_return_60m",
    "future_return_1d",
    "future_return_3d",
    "future_return_5d",
    "eligible_30m",
    "eligible_60m",
    "eligible_1d",
    "eligible_3d",
    "eligible_5d",
    "mature_windows",
    "pending_windows",
    "evaluation_status",
    "max_mature_future_return",
    "became_winner",
]


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


def utc_now() -> str:
    return utc_now_dt().isoformat(timespec="seconds")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def ensure_dirs() -> None:
    RESEARCH_DATA.mkdir(parents=True, exist_ok=True)
    STATIC_RESEARCH.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return utc_now_dt()


def maturity_for(ts: datetime, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Return maturity flags by window.

    A near-miss should only be scored for a window once enough time has passed.
    This prevents future/current-day rows from being incorrectly scored as 0.0.
    """
    now = now or utc_now_dt()
    age_minutes = (now - ts).total_seconds() / 60
    is_future = age_minutes < 0
    flags: Dict[str, bool] = {}

    for label, minutes in WINDOWS.items():
        flags[label] = (not is_future) and age_minutes >= minutes

    mature = [label for label, ready in flags.items() if ready]
    pending = [label for label, ready in flags.items() if not ready]

    if is_future:
        status = "future_timestamp_pending"
    elif mature:
        status = "partially_evaluated" if pending else "fully_evaluated"
    else:
        status = "pending_maturity"

    return {
        "age_minutes": round(age_minutes, 2),
        "is_future_timestamp": is_future,
        "flags": flags,
        "mature_windows": mature,
        "pending_windows": pending,
        "evaluation_status": status,
    }


def fetch_candles(symbol: str, start_time: datetime, end_time: datetime):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(start=start_time, end=end_time, interval="30m")
    except Exception:
        return None


def fetch_future_returns(symbol: str, start_time: datetime, maturity: Dict[str, Any]) -> Dict[str, Optional[float]]:
    mature_windows = maturity.get("mature_windows", [])
    if not mature_windows:
        return {key: None for key in WINDOWS}

    max_mature_minutes = max(WINDOWS[label] for label in mature_windows)
    end_time = start_time + timedelta(minutes=max_mature_minutes + 60)

    try:
        hist = fetch_candles(symbol, start_time, end_time)
        if hist is None or hist.empty:
            return {key: None for key in WINDOWS}

        base_price = safe_float(hist["Close"].iloc[0])
        if base_price <= 0:
            return {key: None for key in WINDOWS}

        results: Dict[str, Optional[float]] = {}
        for label, mins in WINDOWS.items():
            if label not in mature_windows:
                results[label] = None
                continue

            target = start_time + timedelta(minutes=mins)
            subset = hist[hist.index <= target]

            if subset.empty:
                results[label] = None
                continue

            max_price = safe_float(subset["High"].max())
            pct = ((max_price - base_price) / base_price) * 100
            results[label] = round(pct, 2)

        return results

    except Exception:
        return {key: None for key in WINDOWS}


def max_mature_return(returns: Dict[str, Optional[float]]) -> Optional[float]:
    values = [value for value in returns.values() if value is not None]
    if not values:
        return None
    return round(max(values), 2)


def evaluate_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    evaluated = []
    now = utc_now_dt()

    for row in rows:
        symbol = str(row.get("symbol") or "").upper().strip()
        if not symbol:
            continue

        ts = parse_timestamp(row.get("timestamp") or utc_now())
        maturity = maturity_for(ts, now=now)
        returns = fetch_future_returns(symbol, ts, maturity)
        max_return = max_mature_return(returns)
        became_winner = bool(max_return is not None and max_return >= WINNER_THRESHOLD)

        evaluated.append({
            "symbol": symbol,
            "timestamp": row.get("timestamp", ""),
            "score": safe_float(row.get("score")),
            "nearest_threshold": safe_float(row.get("nearest_threshold")),
            "near_miss_type": row.get("near_miss_type", "unknown"),
            "reason": row.get("reason", ""),
            "future_return_30m": returns.get("30m", ""),
            "future_return_60m": returns.get("60m", ""),
            "future_return_1d": returns.get("1d", ""),
            "future_return_3d": returns.get("3d", ""),
            "future_return_5d": returns.get("5d", ""),
            "eligible_30m": maturity["flags"].get("30m", False),
            "eligible_60m": maturity["flags"].get("60m", False),
            "eligible_1d": maturity["flags"].get("1d", False),
            "eligible_3d": maturity["flags"].get("3d", False),
            "eligible_5d": maturity["flags"].get("5d", False),
            "mature_windows": ",".join(maturity["mature_windows"]),
            "pending_windows": ",".join(maturity["pending_windows"]),
            "evaluation_status": maturity["evaluation_status"],
            "max_mature_future_return": max_return if max_return is not None else "",
            "became_winner": became_winner,
        })

        # Small pause to avoid hammering yfinance when run manually/scheduled.
        time.sleep(0.2)

    return evaluated


def mature_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if r.get("max_mature_future_return") not in (None, "")]


def row_return(row: Dict[str, Any]) -> float:
    return safe_float(row.get("max_mature_future_return"), 0.0)


def row_is_bad_signal(row: Dict[str, Any]) -> bool:
    return row_return(row) <= BAD_SIGNAL_THRESHOLD


def confidence_from_sample(sample_size: int) -> str:
    if sample_size >= MIN_EVALUATED_FOR_HIGH:
        return "HIGH"
    if sample_size >= MIN_EVALUATED_FOR_MEDIUM:
        return "MEDIUM"
    return "LOW"


def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    mature = mature_rows(rows)
    pending = [r for r in rows if r not in mature]

    if not mature:
        return {
            "total_rows": len(rows),
            "evaluated_count": 0,
            "pending_count": len(pending),
            "winner_rate": 0,
            "avg_future_return": 0,
            "strongest_rejection_reason": "none",
            "threshold_pressure": "insufficient_mature_data",
            "confidence": "LOW",
        }

    winners = [r for r in mature if r["became_winner"]]
    avg_return = sum(row_return(r) for r in mature) / max(len(mature), 1)

    reason_counts = defaultdict(int)
    for r in winners:
        reason_counts[r.get("near_miss_type") or "unknown"] += 1

    strongest_reason = max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else "none"
    sample_size = len(mature)

    pressure = "moderate" if winners else "low"
    if winners and (len(winners) / max(sample_size, 1)) >= 0.2:
        pressure = "high"

    return {
        "total_rows": len(rows),
        "evaluated_count": sample_size,
        "pending_count": len(pending),
        "winner_rate": round((len(winners) / sample_size) * 100, 2),
        "avg_future_return": round(avg_return, 2),
        "strongest_rejection_reason": strongest_reason,
        "threshold_pressure": pressure,
        "confidence": confidence_from_sample(sample_size),
    }


def threshold_stats(rows: List[Dict[str, Any]], threshold: int) -> Dict[str, Any]:
    kept = [r for r in rows if safe_float(r["score"]) >= threshold]
    rejected = [r for r in rows if safe_float(r["score"]) < threshold]
    winners_kept = [r for r in kept if r["became_winner"]]
    bad_kept = [r for r in kept if row_is_bad_signal(r)]
    missed_winners = [r for r in rejected if r["became_winner"]]
    returns = [row_return(r) for r in kept]

    return {
        "threshold": threshold,
        "opportunities_kept": len(kept),
        "opportunities_rejected": len(rejected),
        "winner_count": len(winners_kept),
        "bad_signal_count": len(bad_kept),
        "missed_winners": len(missed_winners),
        "winner_rate": round((len(winners_kept) / max(len(kept), 1)) * 100, 2),
        "bad_signal_rate": round((len(bad_kept) / max(len(kept), 1)) * 100, 2),
        "avg_return": round(sum(returns) / max(len(returns), 1), 2),
        "mature_only": True,
        "recommendation_only": True,
    }


def threshold_delta_analysis(diagnostics: Dict[str, Dict[str, Any]], baseline: int = BASELINE_THRESHOLD) -> Dict[str, Any]:
    baseline_stats = diagnostics.get(str(baseline), {})
    out: Dict[str, Any] = {}

    for threshold in THRESHOLDS:
        stats = diagnostics.get(str(threshold), {})
        delta = baseline - threshold
        extra_opportunities = int(stats.get("opportunities_kept", 0)) - int(baseline_stats.get("opportunities_kept", 0))
        expected_extra_winners = int(stats.get("winner_count", 0)) - int(baseline_stats.get("winner_count", 0))
        expected_extra_bad_signals = int(stats.get("bad_signal_count", 0)) - int(baseline_stats.get("bad_signal_count", 0))
        avg_return_delta = round(safe_float(stats.get("avg_return")) - safe_float(baseline_stats.get("avg_return")), 2)

        if extra_opportunities <= 0:
            verdict = "same_or_stricter_than_baseline"
        elif expected_extra_winners > expected_extra_bad_signals and avg_return_delta >= -0.5:
            verdict = "promising_research_only"
        elif expected_extra_bad_signals > expected_extra_winners:
            verdict = "risk_increases_faster_than_edge"
        else:
            verdict = "inconclusive"

        out[str(threshold)] = {
            "threshold_delta_from_baseline": delta,
            "extra_opportunities_vs_baseline": extra_opportunities,
            "expected_extra_winners": expected_extra_winners,
            "expected_extra_bad_signals": expected_extra_bad_signals,
            "avg_return_delta_vs_baseline": avg_return_delta,
            "verdict": verdict,
        }

    return out


def recommendation_from_pressure(mature_count: int, deltas: Dict[str, Any]) -> Dict[str, Any]:
    confidence = confidence_from_sample(mature_count)
    if mature_count < MIN_EVALUATED_FOR_MEDIUM:
        return {
            "action": "collect_more_data",
            "recommended_threshold": None,
            "confidence": confidence,
            "reason": "Mature near-miss sample size is below 30. Do not tune live thresholds yet.",
            "automation_allowed": False,
        }

    promising = []
    for threshold, row in deltas.items():
        if row.get("verdict") == "promising_research_only" and int(threshold) < BASELINE_THRESHOLD:
            promising.append((int(threshold), row))

    if not promising:
        return {
            "action": "hold_thresholds",
            "recommended_threshold": BASELINE_THRESHOLD,
            "confidence": confidence,
            "reason": "No mature threshold test currently improves winners without increasing risk.",
            "automation_allowed": False,
        }

    # Prefer the least aggressive promising cut first.
    selected_threshold, selected = sorted(promising, key=lambda item: item[0], reverse=True)[0]
    return {
        "action": "research_only_watch_lower_threshold",
        "recommended_threshold": selected_threshold,
        "confidence": confidence,
        "reason": "A slightly lower threshold produced better mature near-miss capture in research-only simulation.",
        "details": selected,
        "automation_allowed": False,
    }


def build_threshold_pressure(rows: List[Dict[str, Any]], runtime_ms: int = 0) -> Dict[str, Any]:
    mature = mature_rows(rows)
    diagnostics = {str(threshold): threshold_stats(mature, threshold) for threshold in THRESHOLDS}
    deltas = threshold_delta_analysis(diagnostics, baseline=BASELINE_THRESHOLD)
    recommendation = recommendation_from_pressure(len(mature), deltas)

    payload = {
        "status": "ok",
        "version": "threshold_pressure_v2_mature_only",
        "updated_at": utc_now(),
        "runtime_ms": runtime_ms,
        "records": len(rows),
        "mature_records": len(mature),
        "pending_records": max(0, len(rows) - len(mature)),
        "baseline_threshold": BASELINE_THRESHOLD,
        "winner_threshold_pct": WINNER_THRESHOLD,
        "bad_signal_threshold_pct": BAD_SIGNAL_THRESHOLD,
        "source": "near_miss_outcome_evaluator",
        "thresholds": diagnostics,
        "threshold_delta_analysis": deltas,
        "recommendation": recommendation,
        "notes": [
            "Threshold pressure uses mature rows only.",
            "Pending/future rows are excluded to avoid false negatives.",
            "This is recommendation-only and never changes live thresholds.",
            "automation_allowed is always false for this module.",
        ],
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
        },
    }

    THRESHOLD_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> Dict[str, Any]:
    start = time.time()
    ensure_dirs()

    source_rows = read_csv(INPUT_CSV)
    evaluated = evaluate_rows(source_rows)
    write_csv(evaluated, OUTCOME_CSV)

    runtime_ms = int((time.time() - start) * 1000)
    summary = build_summary(evaluated)
    mature = mature_rows(evaluated)
    threshold_payload = build_threshold_pressure(evaluated, runtime_ms=runtime_ms)

    payload = {
        "status": "ok",
        "version": "near_miss_outcome_evaluator_v1.2",
        "updated_at": utc_now(),
        "runtime_ms": runtime_ms,
        "records": len(evaluated),
        "mature_records": len(mature),
        "pending_records": max(0, len(evaluated) - len(mature)),
        "source": "near_miss_outcome_evaluator",
        "summary": summary,
        "threshold_pressure_summary": {
            "baseline_threshold": BASELINE_THRESHOLD,
            "recommendation": threshold_payload.get("recommendation", {}),
            "mature_records": threshold_payload.get("mature_records", 0),
        },
        "top_winners": sorted(
            mature,
            key=lambda r: safe_float(r.get("max_mature_future_return")),
            reverse=True,
        )[:15],
        "pending_examples": [
            r for r in evaluated if r.get("evaluation_status") in {"pending_maturity", "future_timestamp_pending"}
        ][:15],
        "notes": [
            "Only mature outcome windows are used for winner_rate and threshold pressure.",
            "Too-new/future rows are marked pending instead of scored as failures.",
            "Threshold pressure diagnostics are recommendation-only and never change live trading behavior.",
            "This file is research-only and never changes live trading behavior.",
        ],
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
        },
    }

    OUTCOME_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
