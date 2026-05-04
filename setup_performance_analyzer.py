"""
Research-only setup performance analyzer for Ponder Invest AI.

This module reads existing shadow/forward evaluation JSON and creates setup-level
analytics. It does not place orders, modify Alpaca execution, rotate positions,
or change live bot logic.

Manual run:
    python3 setup_performance_analyzer.py

Outputs:
    static/research/setup_performance_latest.json
"""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "static" / "research"
PERFORMANCE_FILE = RESEARCH_DIR / "rotation_performance_latest.json"
LEARNING_FILE = RESEARCH_DIR / "shadow_learning_latest.json"
SETUP_PERFORMANCE_FILE = RESEARCH_DIR / "setup_performance_latest.json"

VALID_OUTCOMES = {"helped", "hurt", "neutral"}
SETUP_KEYWORDS = {
    "day_trade_shadow": ("day_trade_shadow", "day trade", "intraday", "day-trade"),
    "momentum": ("momentum", "relative strength", "strong trend", "trend continuation"),
    "breakout": ("breakout", "break out", "new high", "resistance break"),
    "pullback": ("pullback", "dip", "bounce", "support", "mean reversion"),
    "oversold": ("oversold", "rsi low", "capitulation"),
    "sell_warning": ("sell warning", "sell intelligence", "trim", "exit", "bearish"),
    "capital_rotation": ("rotation", "rotate", "allocator", "capital", "opportunity cost"),
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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=False, default=str))
    os.replace(tmp, path)


def clean_text(value: Any, default: str = "") -> str:
    if value in (None, "", "undefined", "None"):
        return default
    return str(value).strip()


def clean_number(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, "", "undefined", "nan", "None"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def safe_percent(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round((numerator / denominator) * 100, 2)


def normalized_slug(value: str) -> str:
    slug = clean_text(value, "").lower()
    slug = slug.replace("-", "_").replace("/", "_")
    slug = "_".join(part for part in slug.split() if part)
    return slug or "unlabeled"


def infer_setup(record: Dict[str, Any]) -> str:
    """Return the best available setup label for one research/evaluation row."""
    explicit = clean_text(
        record.get("setup")
        or record.get("setup_label")
        or record.get("entry_setup")
        or record.get("signal_setup")
        or record.get("candidate_setup"),
        "",
    )
    if explicit:
        return normalized_slug(explicit)

    haystack = " ".join(
        clean_text(record.get(name), "")
        for name in ("reason", "entry_reason", "action", "recommendation", "notes", "type")
    ).lower()
    for setup, keywords in SETUP_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return setup

    idea_type = normalized_slug(clean_text(record.get("type"), "research"))
    if idea_type in {"sell", "trim", "exit"}:
        return "sell_warning"
    if idea_type == "rotation":
        return "capital_rotation"
    return "unlabeled_research"


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(record)
    row["setup"] = infer_setup(row)
    row["type"] = normalized_slug(clean_text(row.get("type"), "research"))
    row["status"] = normalized_slug(clean_text(row.get("status"), "pending"))

    outcome = normalized_slug(clean_text(row.get("outcome") or row.get("result"), ""))
    row["outcome"] = outcome if outcome in VALID_OUTCOMES else None
    if row["outcome"] in VALID_OUTCOMES:
        row["status"] = "evaluated"

    alpha = clean_number(row.get("alpha"), None)
    alpha_pct = clean_number(row.get("alpha_pct") or row.get("avg_alpha_pct"), None)
    if alpha is None and alpha_pct is not None:
        alpha = alpha_pct / 100.0
    if alpha_pct is None and alpha is not None:
        alpha_pct = alpha * 100.0
    row["alpha"] = round(alpha, 6) if alpha is not None else None
    row["alpha_pct"] = round(alpha_pct, 4) if alpha_pct is not None else None
    return row


def load_evaluations() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in (PERFORMANCE_FILE, LEARNING_FILE):
        data = read_json(path, {})
        for row in data.get("evaluations") or data.get("records") or []:
            if isinstance(row, dict):
                records.append(row)

    # Dedupe by id when available, otherwise by stable research fields.
    deduped: Dict[str, Dict[str, Any]] = {}
    for row in records:
        key = clean_text(row.get("id"), "") or "|".join(
            clean_text(row.get(name), "")
            for name in ("signal_timestamp", "type", "from_symbol", "to_symbol", "horizon", "action")
        )
        normalized = normalize_record(row)
        existing = deduped.get(key)
        if existing is None or existing.get("status") != "evaluated":
            deduped[key] = normalized
    return list(deduped.values())


def summarize_by_setup(records: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total": 0,
        "evaluated": 0,
        "pending": 0,
        "waiting_for_market_data": 0,
        "helped": 0,
        "hurt": 0,
        "neutral": 0,
        "win_rate": None,
        "avg_alpha": None,
        "avg_alpha_pct": None,
        "best_alpha_pct": None,
        "worst_alpha_pct": None,
        "sample_warning": "No evaluated samples yet",
    })

    alphas_by_setup: Dict[str, List[float]] = defaultdict(list)
    for row in records:
        setup = infer_setup(row)
        bucket = buckets[setup]
        bucket["total"] += 1

        status = clean_text(row.get("status"), "pending")
        outcome = clean_text(row.get("outcome"), "")
        if status == "evaluated" and outcome in VALID_OUTCOMES:
            bucket["evaluated"] += 1
            bucket[outcome] += 1
            alpha = clean_number(row.get("alpha"), None)
            if alpha is not None:
                alphas_by_setup[setup].append(alpha)
        else:
            bucket["pending"] += 1
            if status == "waiting_for_market_data":
                bucket["waiting_for_market_data"] += 1

    for setup, bucket in buckets.items():
        evaluated = bucket["evaluated"]
        bucket["win_rate"] = safe_percent(bucket["helped"], evaluated)
        alphas = alphas_by_setup.get(setup, [])
        if alphas:
            avg_alpha = sum(alphas) / len(alphas)
            bucket["avg_alpha"] = round(avg_alpha, 6)
            bucket["avg_alpha_pct"] = round(avg_alpha * 100, 4)
            bucket["best_alpha_pct"] = round(max(alphas) * 100, 4)
            bucket["worst_alpha_pct"] = round(min(alphas) * 100, 4)
        if evaluated >= 10:
            bucket["sample_warning"] = "Enough samples for early directional review"
        elif evaluated > 0:
            bucket["sample_warning"] = "Low sample size; do not optimize yet"

    return dict(sorted(buckets.items(), key=lambda item: (item[1]["evaluated"], item[1]["avg_alpha_pct"] or -999), reverse=True))


def build_output() -> Dict[str, Any]:
    records = load_evaluations()
    by_setup = summarize_by_setup(records)
    evaluated = [row for row in records if row.get("status") == "evaluated" and row.get("outcome") in VALID_OUTCOMES]
    pending = [row for row in records if row.get("status") != "evaluated"]

    return {
        "updated_at": utc_now(),
        "version": "v2_setup_level_research_only",
        "status": "research_only",
        "summary": {
            "total_records": len(records),
            "evaluated": len(evaluated),
            "pending": len(pending),
            "setup_count": len(by_setup),
            "best_setup": next(iter(by_setup), None),
        },
        "by_setup": by_setup,
        "evaluations": records,
        "notes": [
            "Research-only setup analyzer. Does not place orders or modify live trading logic.",
            "Setup labels are taken from explicit setup fields first, then inferred from action/reason text.",
            "Low sample-size warnings are intentional; do not optimize live trading from tiny samples.",
            "This module intentionally does not overwrite forward_setup_simulations_latest.json.",
        ],
    }


def run_analyzer() -> Dict[str, Any]:
    output = build_output()
    write_json(SETUP_PERFORMANCE_FILE, output)
    return output


def main() -> None:
    output = run_analyzer()
    summary = output.get("summary", {})
    print("Ponder Setup Performance Analyzer complete")
    print(f"total records: {summary.get('total_records', 0)}")
    print(f"evaluated: {summary.get('evaluated', 0)}")
    print(f"pending: {summary.get('pending', 0)}")
    print(f"setup count: {summary.get('setup_count', 0)}")
    print(f"updated: {SETUP_PERFORMANCE_FILE}")


if __name__ == "__main__":
    main()
