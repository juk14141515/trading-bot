"""Outcome evaluator for shadow setups.

Reads research_data/shadow_setups.csv and/or backfilled CSVs, computes simple
performance metrics, and writes a dashboard JSON snapshot.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "research_data"
OUT = ROOT / "static" / "research" / "setup_outcomes_latest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def load_all_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for p in RESEARCH_DIR.glob("*.csv"):
        rows.extend(read_csv(p))
    return rows


def evaluate(rows: List[Dict[str, str]]) -> Dict[str, object]:
    by_setup = defaultdict(lambda: {"count": 0, "wins": 0, "losses": 0, "avg_r1d": 0.0, "avg_r5d": 0.0, "scores": []})
    outcomes = Counter()

    for r in rows:
        setup = r.get("setup_type", "unknown")
        o = r.get("outcome", "unknown")
        r1 = safe_float(r.get("next_1d_return"))
        r5 = safe_float(r.get("next_5d_return"))
        score = safe_float(r.get("score"))

        d = by_setup[setup]
        d["count"] += 1
        d["scores"].append(score)
        d["avg_r1d"] += r1
        d["avg_r5d"] += r5

        outcomes[o] += 1
        if o == "winner":
            d["wins"] += 1
        elif o == "loser":
            d["losses"] += 1

    result = {}
    for k, d in by_setup.items():
        n = max(1, d["count"])
        result[k] = {
            "count": d["count"],
            "win_rate": round((d["wins"] / n) * 100, 2),
            "loss_rate": round((d["losses"] / n) * 100, 2),
            "avg_1d": round(d["avg_r1d"] / n, 3),
            "avg_5d": round(d["avg_r5d"] / n, 3),
            "avg_score": round(sum(d["scores"]) / n, 2) if d["scores"] else 0,
        }

    return {"setups": result, "outcomes": dict(outcomes), "total_rows": len(rows)}


def main() -> Dict[str, object]:
    rows = load_all_rows()
    data = evaluate(rows)
    out = {"generated_at": utc_now(), **data}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True))
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
