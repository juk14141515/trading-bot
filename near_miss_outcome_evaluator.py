"""Research-only near miss outcome evaluator for Ponder Invest AI.

Evaluates whether near-miss/rejected candidates later became strong performers.
This module NEVER modifies live trading logic, Alpaca execution, thresholds,
or bot.py behavior.
"""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

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
WINNER_THRESHOLD = 3.0


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
    "max_future_return",
    "became_winner",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")



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
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)



def fetch_future_returns(symbol: str, start_time: datetime) -> Dict[str, float]:
    end_time = start_time + timedelta(days=7)

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_time, end=end_time, interval="30m")

        if hist.empty:
            return {key: 0.0 for key in WINDOWS}

        base_price = safe_float(hist["Close"].iloc[0])
        if base_price <= 0:
            return {key: 0.0 for key in WINDOWS}

        results = {}

        for label, mins in WINDOWS.items():
            target = start_time + timedelta(minutes=mins)
            subset = hist[hist.index <= target]

            if subset.empty:
                results[label] = 0.0
                continue

            max_price = safe_float(subset["High"].max())
            pct = ((max_price - base_price) / base_price) * 100
            results[label] = round(pct, 2)

        return results

    except Exception:
        return {key: 0.0 for key in WINDOWS}



def evaluate_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    evaluated = []

    for row in rows:
        symbol = str(row.get("symbol") or "").upper().strip()
        if not symbol:
            continue

        ts = parse_timestamp(row.get("timestamp") or utc_now())
        returns = fetch_future_returns(symbol, ts)

        max_return = max(returns.values()) if returns else 0.0

        evaluated.append({
            "symbol": symbol,
            "timestamp": row.get("timestamp", ""),
            "score": safe_float(row.get("score")),
            "nearest_threshold": safe_float(row.get("nearest_threshold")),
            "near_miss_type": row.get("near_miss_type", "unknown"),
            "reason": row.get("reason", ""),
            "future_return_30m": returns.get("30m", 0.0),
            "future_return_60m": returns.get("60m", 0.0),
            "future_return_1d": returns.get("1d", 0.0),
            "future_return_3d": returns.get("3d", 0.0),
            "future_return_5d": returns.get("5d", 0.0),
            "max_future_return": round(max_return, 2),
            "became_winner": max_return >= WINNER_THRESHOLD,
        })

        time.sleep(0.2)

    return evaluated



def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "evaluated_count": 0,
            "winner_rate": 0,
            "avg_future_return": 0,
            "strongest_rejection_reason": "none",
            "threshold_pressure": "insufficient_data",
            "confidence": "LOW",
        }

    winners = [r for r in rows if r["became_winner"]]
    avg_return = sum(r["max_future_return"] for r in rows) / max(len(rows), 1)

    reason_counts = defaultdict(int)
    for r in winners:
        reason_counts[r.get("near_miss_type") or "unknown"] += 1

    strongest_reason = max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else "none"

    sample_size = len(rows)

    if sample_size >= 100:
        confidence = "HIGH"
    elif sample_size >= 30:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "evaluated_count": sample_size,
        "winner_rate": round((len(winners) / sample_size) * 100, 2),
        "avg_future_return": round(avg_return, 2),
        "strongest_rejection_reason": strongest_reason,
        "threshold_pressure": "moderate" if len(winners) > 0 else "low",
        "confidence": confidence,
    }



def build_threshold_pressure(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    diagnostics = {}

    for threshold in THRESHOLDS:
        kept = [r for r in rows if safe_float(r["score"]) >= threshold]
        rejected = [r for r in rows if safe_float(r["score"]) < threshold]
        missed_winners = [r for r in rejected if r["became_winner"]]

        diagnostics[str(threshold)] = {
            "opportunities_kept": len(kept),
            "opportunities_rejected": len(rejected),
            "winner_rate": round(
                (len([r for r in kept if r["became_winner"]]) / max(len(kept), 1)) * 100,
                2,
            ),
            "avg_return": round(
                sum(r["max_future_return"] for r in kept) / max(len(kept), 1),
                2,
            ),
            "missed_winners": len(missed_winners),
            "recommendation_only": True,
        }

    payload = {
        "status": "ok",
        "updated_at": utc_now(),
        "runtime_ms": 0,
        "records": len(rows),
        "source": "near_miss_outcome_evaluator",
        "thresholds": diagnostics,
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
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

    payload = {
        "status": "ok",
        "updated_at": utc_now(),
        "runtime_ms": runtime_ms,
        "records": len(evaluated),
        "source": "near_miss_outcome_evaluator",
        "summary": summary,
        "top_winners": sorted(
            evaluated,
            key=lambda r: r["max_future_return"],
            reverse=True,
        )[:15],
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
        },
    }

    OUTCOME_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True))

    build_threshold_pressure(evaluated)

    print(json.dumps(payload, indent=2, sort_keys=True))

    return payload


if __name__ == "__main__":
    main()
