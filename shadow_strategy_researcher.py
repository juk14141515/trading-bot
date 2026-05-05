"""Shadow-only strategy researcher for Ponder Invest AI.

Reads historical setup CSVs and setup outcome summaries, then writes research
recommendations for setup priority, threshold ideas, and shadow-only allocation
bias. This module never imports bot.py and never places orders.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
OUT_DIR = ROOT / "static" / "research"
OUT_FILE = OUT_DIR / "shadow_strategy_research_latest.json"

MIN_SAMPLE = 50
THRESHOLDS = [60, 65, 68, 70, 72, 75, 78, 80, 85, 90]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def load_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in sorted(RESEARCH_DATA.glob("*.csv")):
        for row in read_csv(path):
            row["source_file"] = path.name
            rows.append(row)
    return rows


def summarize(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, float]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get("setup_type", "unknown")].append(row)

    out: Dict[str, Dict[str, float]] = {}
    for setup, items in grouped.items():
        n = len(items)
        wins = sum(1 for r in items if r.get("outcome") == "winner")
        losses = sum(1 for r in items if r.get("outcome") == "loser")
        avg_1d = sum(safe_float(r.get("next_1d_return")) for r in items) / max(1, n)
        avg_5d = sum(safe_float(r.get("next_5d_return")) for r in items) / max(1, n)
        avg_score = sum(safe_float(r.get("score")) for r in items) / max(1, n)
        edge_score = (avg_5d * 10) + ((wins / max(1, n)) * 20) - ((losses / max(1, n)) * 15)
        out[setup] = {
            "count": n,
            "win_rate": round((wins / max(1, n)) * 100, 2),
            "loss_rate": round((losses / max(1, n)) * 100, 2),
            "avg_1d": round(avg_1d, 3),
            "avg_5d": round(avg_5d, 3),
            "avg_score": round(avg_score, 2),
            "edge_score": round(edge_score, 3),
        }
    return out


def threshold_tests(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, float]]]:
    by_setup = defaultdict(list)
    for row in rows:
        by_setup[row.get("setup_type", "unknown")].append(row)

    output: Dict[str, List[Dict[str, float]]] = {}
    for setup, items in by_setup.items():
        tests = []
        for threshold in THRESHOLDS:
            filtered = [r for r in items if safe_float(r.get("score")) >= threshold]
            n = len(filtered)
            if n < MIN_SAMPLE:
                continue
            wins = sum(1 for r in filtered if r.get("outcome") == "winner")
            losses = sum(1 for r in filtered if r.get("outcome") == "loser")
            avg_5d = sum(safe_float(r.get("next_5d_return")) for r in filtered) / max(1, n)
            quality = (avg_5d * 10) + ((wins / n) * 20) - ((losses / n) * 15)
            tests.append({
                "threshold": threshold,
                "count": n,
                "win_rate": round((wins / n) * 100, 2),
                "loss_rate": round((losses / n) * 100, 2),
                "avg_5d": round(avg_5d, 3),
                "quality_score": round(quality, 3),
            })
        output[setup] = sorted(tests, key=lambda x: x["quality_score"], reverse=True)
    return output


def build_recommendations(summary: Dict[str, Dict[str, float]], tests: Dict[str, List[Dict[str, float]]]) -> List[Dict[str, object]]:
    recs = []
    for setup, stats in summary.items():
        best_test = tests.get(setup, [{}])[0] if tests.get(setup) else {}
        count = stats.get("count", 0)
        avg_5d = stats.get("avg_5d", 0)
        loss_rate = stats.get("loss_rate", 0)
        edge = stats.get("edge_score", 0)

        if count < MIN_SAMPLE:
            action = "collect_more_data"
        elif avg_5d >= 1.0 and loss_rate <= 32:
            action = "shadow_priority"
        elif avg_5d > 0 and edge > 5:
            action = "shadow_watch"
        else:
            action = "deprioritize_shadow"

        recs.append({
            "setup_type": setup,
            "action": action,
            "suggested_threshold": best_test.get("threshold", "collect_more"),
            "sample_size": count,
            "edge_score": edge,
            "avg_5d": avg_5d,
            "win_rate": stats.get("win_rate", 0),
            "loss_rate": loss_rate,
            "reason": f"avg_5d={avg_5d}, loss_rate={loss_rate}, sample={count}",
        })
    return sorted(recs, key=lambda x: x["edge_score"], reverse=True)


def main() -> Dict[str, object]:
    rows = load_rows()
    summary = summarize(rows)
    tests = threshold_tests(rows)
    recommendations = build_recommendations(summary, tests)
    output = {
        "generated_at": utc_now(),
        "mode": "shadow_only_research",
        "total_rows": len(rows),
        "summary": summary,
        "threshold_tests": tests,
        "recommendations": recommendations,
        "notes": [
            "Research-only: does not place trades or modify live bot logic.",
            "Use recommendations for shadow weighting first, not live execution.",
            "Historical backfill is useful for direction, but live shadow data should confirm before automation.",
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(output, indent=2, sort_keys=True))
    return output


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
