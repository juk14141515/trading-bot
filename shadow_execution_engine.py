"""Shadow-only execution engine for Ponder Invest AI.

Compares strategy-research recommendations against historical setup rows and
writes a dashboard-friendly JSON report. This module never imports bot.py,
never calls Alpaca, and never places orders.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
RESEARCH_OUT = ROOT / "static" / "research"
STRATEGY_RESEARCH = RESEARCH_OUT / "shadow_strategy_research_latest.json"
OUT = RESEARCH_OUT / "shadow_execution_latest.json"

DEFAULT_THRESHOLDS = {
    "gap_up_gap_down": 70,
    "earnings_reaction": 60,
    "crypto_momentum": 90,
    "small_cap_breakout": 80,
    "day_trade_momentum": 90,
    "large_cap_pullback": 70,
    "ipo_recent": 60,
    "etf_trend": 999,
}

DEFAULT_ACTIONS = {
    "gap_up_gap_down": "shadow_priority",
    "earnings_reaction": "shadow_priority",
    "crypto_momentum": "shadow_watch",
    "small_cap_breakout": "shadow_watch",
    "day_trade_momentum": "shadow_watch",
    "large_cap_pullback": "shadow_watch",
    "ipo_recent": "shadow_watch",
    "etf_trend": "deprioritize_shadow",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value, default=0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
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


def load_policy() -> Dict[str, Dict[str, object]]:
    data = read_json(STRATEGY_RESEARCH, {})
    policy: Dict[str, Dict[str, object]] = {}
    for rec in data.get("recommendations", []):
        setup = rec.get("setup_type")
        if not setup:
            continue
        threshold = rec.get("suggested_threshold", DEFAULT_THRESHOLDS.get(setup, 999))
        if not isinstance(threshold, (int, float)):
            threshold = DEFAULT_THRESHOLDS.get(setup, 999)
        policy[setup] = {
            "action": rec.get("action", DEFAULT_ACTIONS.get(setup, "shadow_watch")),
            "threshold": safe_float(threshold, DEFAULT_THRESHOLDS.get(setup, 999)),
            "edge_score": safe_float(rec.get("edge_score")),
            "reason": rec.get("reason", "research recommendation"),
        }
    for setup, threshold in DEFAULT_THRESHOLDS.items():
        policy.setdefault(setup, {
            "action": DEFAULT_ACTIONS.get(setup, "shadow_watch"),
            "threshold": threshold,
            "edge_score": 0,
            "reason": "default fallback policy",
        })
    return policy


def should_shadow_execute(row: Dict[str, str], policy: Dict[str, Dict[str, object]]) -> Tuple[bool, str, Dict[str, object]]:
    setup = row.get("setup_type", "unknown")
    score = safe_float(row.get("score"))
    rule = policy.get(setup, {"action": "deprioritize_shadow", "threshold": 999, "reason": "no policy"})
    threshold = safe_float(rule.get("threshold"), 999)
    action = str(rule.get("action", "shadow_watch"))
    if action == "deprioritize_shadow":
        return False, "deprioritized setup", rule
    if score < threshold:
        return False, f"score {score} below shadow threshold {threshold}", rule
    return True, f"score {score} passed shadow threshold {threshold}", rule


def summarize(trades: List[Dict[str, object]]) -> Dict[str, object]:
    n = len(trades)
    wins = [t for t in trades if t.get("outcome") == "winner"]
    losses = [t for t in trades if t.get("outcome") == "loser"]
    returns_1d = [safe_float(t.get("next_1d_return")) for t in trades]
    returns_5d = [safe_float(t.get("next_5d_return")) for t in trades]
    by_setup = defaultdict(list)
    for t in trades:
        by_setup[t.get("setup_type", "unknown")].append(t)

    setup_summary = {}
    for setup, items in by_setup.items():
        count = len(items)
        swins = [x for x in items if x.get("outcome") == "winner"]
        slosses = [x for x in items if x.get("outcome") == "loser"]
        setup_summary[setup] = {
            "count": count,
            "win_rate": round((len(swins) / max(1, count)) * 100, 2),
            "loss_rate": round((len(slosses) / max(1, count)) * 100, 2),
            "avg_1d": round(sum(safe_float(x.get("next_1d_return")) for x in items) / max(1, count), 3),
            "avg_5d": round(sum(safe_float(x.get("next_5d_return")) for x in items) / max(1, count), 3),
            "avg_score": round(sum(safe_float(x.get("score")) for x in items) / max(1, count), 2),
        }

    return {
        "simulated_trades": n,
        "win_rate": round((len(wins) / max(1, n)) * 100, 2),
        "loss_rate": round((len(losses) / max(1, n)) * 100, 2),
        "avg_1d": round(sum(returns_1d) / max(1, n), 3),
        "avg_5d": round(sum(returns_5d) / max(1, n), 3),
        "outcomes": dict(Counter(t.get("outcome", "unknown") for t in trades)),
        "by_setup": dict(sorted(setup_summary.items(), key=lambda kv: kv[1]["avg_5d"], reverse=True)),
    }


def main() -> Dict[str, object]:
    rows = load_rows()
    policy = load_policy()
    selected: List[Dict[str, object]] = []
    rejected = Counter()

    for row in rows:
        ok, decision_reason, rule = should_shadow_execute(row, policy)
        if not ok:
            rejected[decision_reason] += 1
            continue
        selected.append({
            "timestamp": row.get("timestamp"),
            "symbol": row.get("symbol"),
            "setup_type": row.get("setup_type"),
            "score": safe_float(row.get("score")),
            "entry_price": safe_float(row.get("entry_price")),
            "next_1d_return": safe_float(row.get("next_1d_return")),
            "next_3d_return": safe_float(row.get("next_3d_return")),
            "next_5d_return": safe_float(row.get("next_5d_return")),
            "outcome": row.get("outcome", "unknown"),
            "shadow_action": rule.get("action"),
            "shadow_threshold": rule.get("threshold"),
            "decision_reason": decision_reason,
            "why": rule.get("reason"),
        })

    summary = summarize(selected)
    output = {
        "generated_at": utc_now(),
        "mode": "shadow_only_execution_simulation",
        "total_source_rows": len(rows),
        "policy": policy,
        "summary": summary,
        "top_shadow_trades": sorted(selected, key=lambda x: safe_float(x.get("score")), reverse=True)[:25],
        "rejected_counts": dict(rejected.most_common(20)),
        "explanation": [
            "This is a read-only simulation. It does not change live trading logic.",
            "The engine reads setup recommendations, applies setup-specific thresholds, and simulates which trades would have passed shadow rules.",
            "Use this to validate strategy ideas before any live scoring or capital-allocation change.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True))
    return output


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
