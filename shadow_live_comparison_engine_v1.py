"""Shadow vs Live Comparison Engine for Ponder Invest AI.

Research-only. Compares actual bot trade history against shadow setup
opportunities and writes a dashboard-friendly JSON report.

Safety guarantees:
- never imports bot.py
- never calls Alpaca
- never places orders
- never changes live trading, risk, scoring, or capital-allocation behavior
- handles missing/partial data without crashing cron jobs
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA = ROOT / "research_data"
RESEARCH_OUT = ROOT / "static" / "research"
TRADE_HISTORY = ROOT / "trade_history.csv"
SHADOW_SETUPS = RESEARCH_DATA / "shadow_setups.csv"
SHADOW_EXECUTION = RESEARCH_OUT / "shadow_execution_latest.json"
SETUP_OUTCOMES = RESEARCH_OUT / "setup_outcomes_latest.json"
TOP_CANDIDATES = ROOT / "top_10_candidates_v2.json"
OUT_FILE = RESEARCH_OUT / "shadow_live_comparison_latest.json"

WINNER_OUTCOMES = {"winner", "missed_opportunity", "early_exit"}
BAD_OUTCOMES = {"loser", "false_signal", "late_exit"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, "", "None", "nan", "NaN"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def safe_round(value: Any, digits: int = 3) -> Optional[float]:
    number = safe_float(value)
    if number is None:
        return None
    return round(number, digits)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], Optional[str]]:
    if not path.exists():
        return [], f"missing: {path.name}"
    try:
        with path.open(newline="") as f:
            return list(csv.DictReader(f)), None
    except Exception as exc:
        return [], f"error reading {path.name}: {type(exc).__name__}: {exc}"


def read_json(path: Path, default: Any) -> Tuple[Any, Optional[str]]:
    if not path.exists():
        return default, f"missing: {path.name}"
    try:
        return json.loads(path.read_text()), None
    except Exception as exc:
        return default, f"error reading {path.name}: {type(exc).__name__}: {exc}"


def first_value(row: Dict[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", "None", "nan", "NaN"):
            return value
    return default


def parse_timestamp(value: Any) -> Tuple[str, str]:
    """Return (iso-ish timestamp, yyyy-mm-dd key)."""
    raw = str(value or "").strip()
    if not raw:
        return "", ""
    # Common CSV/date forms: ISO, '2026-05-04 13:30:00', pandas Timestamp string.
    clean = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(clean)
        return parsed.isoformat(), parsed.date().isoformat()
    except Exception:
        # Fallback: first 10 chars usually preserve YYYY-MM-DD.
        return raw, raw[:10] if len(raw) >= 10 else raw


def normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def infer_return_pct(row: Dict[str, Any], preferred_keys: Iterable[str]) -> Optional[float]:
    for key in preferred_keys:
        value = safe_float(row.get(key))
        if value is not None:
            # Alpaca unrealized_plpc style can be decimal fraction; convert likely fractions.
            if key.endswith("pc") or key.endswith("pct_decimal"):
                return value * 100
            return value

    pnl = safe_float(first_value(row, ("pnl", "pl", "realized_pl", "profit_loss", "net_pl")))
    cost = safe_float(first_value(row, ("cost_basis", "entry_value", "notional", "buy_value")))
    if pnl is not None and cost not in (None, 0):
        return (pnl / cost) * 100

    entry = safe_float(first_value(row, ("entry_price", "buy_price", "avg_entry_price", "average_entry_price")))
    exit_price = safe_float(first_value(row, ("exit_price", "sell_price", "close_price", "current_price")))
    if entry not in (None, 0) and exit_price is not None:
        return ((exit_price - entry) / entry) * 100
    return None


def normalize_live_trade(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    symbol = normalize_symbol(first_value(row, ("symbol", "ticker", "asset")))
    if not symbol:
        return None
    timestamp, day = parse_timestamp(first_value(row, ("exit_time", "closed_at", "timestamp", "time", "date", "entry_time", "created_at")))
    setup_type = str(first_value(row, ("setup_type", "strategy", "signal", "label", "source"), "unknown") or "unknown")
    return_pct = infer_return_pct(row, (
        "return_pct", "return", "pnl_pct", "pl_pct", "profit_pct", "realized_pl_pct", "unrealized_plpc",
    ))
    outcome_raw = str(first_value(row, ("outcome", "result", "status"), "") or "").lower()
    bad = False
    if return_pct is not None and return_pct < 0:
        bad = True
    if outcome_raw in BAD_OUTCOMES:
        bad = True
    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "day": day,
        "setup_type": setup_type,
        "return_pct": safe_round(return_pct),
        "outcome": outcome_raw or ("loser" if bad else "unknown"),
        "is_bad_live_trade": bad,
        "raw_source": "trade_history.csv",
    }


def normalize_shadow_row(row: Dict[str, Any], source_file: str = "shadow_setups.csv") -> Optional[Dict[str, Any]]:
    symbol = normalize_symbol(first_value(row, ("symbol", "ticker", "asset")))
    if not symbol:
        return None
    timestamp, day = parse_timestamp(first_value(row, ("timestamp", "time", "date", "created_at")))
    setup_type = str(first_value(row, ("setup_type", "setup", "strategy", "label"), "unknown") or "unknown")
    outcome = str(first_value(row, ("outcome", "result", "status"), "pending") or "pending").lower()
    score = safe_float(first_value(row, ("score", "final_score", "confidence")), 0.0)
    # Prefer 5d for opportunity cost, then 3d/1d/1h when newer data is incomplete.
    return_pct = first_value(row, ("next_5d_return", "next_3d_return", "next_1d_return", "next_1h_return"), "")
    return_pct_num = safe_float(return_pct)
    return {
        "setup_id": str(first_value(row, ("setup_id", "id"), "")),
        "symbol": symbol,
        "timestamp": timestamp,
        "day": day,
        "setup_type": setup_type,
        "score": safe_round(score, 2),
        "entry_price": safe_round(first_value(row, ("entry_price", "price", "last_price")), 4),
        "return_pct": safe_round(return_pct_num),
        "next_1h_return": safe_round(row.get("next_1h_return")),
        "next_1d_return": safe_round(row.get("next_1d_return")),
        "next_3d_return": safe_round(row.get("next_3d_return")),
        "next_5d_return": safe_round(row.get("next_5d_return")),
        "outcome": outcome,
        "market_regime": str(first_value(row, ("market_regime", "regime"), "unknown") or "unknown"),
        "source": str(first_value(row, ("source",), source_file) or source_file),
        "source_file": source_file,
        "reason": str(first_value(row, ("reason", "why", "summary"), "") or ""),
        "is_winner": outcome in WINNER_OUTCOMES or (return_pct_num is not None and return_pct_num >= 2.0),
        "is_bad_signal": outcome in BAD_OUTCOMES or (return_pct_num is not None and return_pct_num < 0),
    }


def load_research_rows() -> Tuple[List[Dict[str, Any]], List[str]]:
    rows: List[Dict[str, Any]] = []
    warnings: List[str] = []
    if not RESEARCH_DATA.exists():
        return rows, ["missing: research_data directory"]

    for path in sorted(RESEARCH_DATA.glob("*.csv")):
        raw_rows, warning = read_csv(path)
        if warning:
            warnings.append(warning)
            continue
        for raw in raw_rows:
            normalized = normalize_shadow_row(raw, source_file=path.name)
            if normalized:
                rows.append(normalized)
    return rows, warnings


def sample_confidence(sample_size: int) -> str:
    if sample_size < 100:
        return "low"
    if sample_size < 300:
        return "medium"
    return "high"


def sample_label(sample_size: int) -> str:
    if sample_size < 100:
        return "informational_only"
    if sample_size < 300:
        return "early_signal"
    return "meaningful_signal"


def avg(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 3)


def group_setup_stats(rows: List[Dict[str, Any]], key: str = "setup_type") -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "unknown")].append(row)
    out = []
    for name, items in grouped.items():
        returns = [safe_float(item.get("return_pct")) for item in items]
        winners = [item for item in items if item.get("is_winner")]
        out.append({
            key: name,
            "sample_size": len(items),
            "sample_label": sample_label(len(items)),
            "confidence": sample_confidence(len(items)),
            "winner_count": len(winners),
            "win_rate": round((len(winners) / max(1, len(items))) * 100, 2),
            "avg_return_pct": avg(returns),
            "basis": sorted({str(item.get("source") or item.get("source_file") or "unknown") for item in items})[:5],
        })
    return sorted(out, key=lambda x: (safe_float(x.get("avg_return_pct"), -999) or -999), reverse=True)


def compare(live_trades: List[Dict[str, Any]], shadow_rows: List[Dict[str, Any]], shadow_execution: Dict[str, Any], setup_outcomes: Dict[str, Any], top_candidates: Any, warnings: List[str]) -> Dict[str, Any]:
    live_keys = {(t.get("symbol"), t.get("day")) for t in live_trades if t.get("symbol") and t.get("day")}
    matched_shadow = [s for s in shadow_rows if (s.get("symbol"), s.get("day")) in live_keys]
    missed_winners = [s for s in shadow_rows if s.get("is_winner") and (s.get("symbol"), s.get("day")) not in live_keys]
    bad_live = [t for t in live_trades if t.get("is_bad_live_trade")]

    live_avg = avg([safe_float(t.get("return_pct")) for t in live_trades])
    shadow_avg = avg([safe_float(s.get("return_pct")) for s in shadow_rows if s.get("return_pct") is not None])
    missed_avg = avg([safe_float(s.get("return_pct")) for s in missed_winners if s.get("return_pct") is not None])
    opportunity_cost = None
    if missed_avg is not None and live_avg is not None:
        opportunity_cost = round(missed_avg - live_avg, 3)

    evaluated_shadow = [s for s in shadow_rows if str(s.get("outcome") or "pending") not in {"", "pending", "unknown"}]
    confidence = sample_confidence(len(evaluated_shadow))
    possible_over_filtering = len(missed_winners) >= 3 and len(missed_winners) > len(live_trades)
    possible_under_filtering = len(bad_live) >= 2 and len(bad_live) >= max(1, int(len(live_trades) * 0.4))

    recommendation_notes: List[Dict[str, Any]] = []
    if len(evaluated_shadow) < 100:
        recommendation_notes.append({
            "type": "research_only",
            "message": "Collect more evaluated shadow/live samples before changing live thresholds.",
            "why": "Evaluated sample size is below 100, so this is informational only.",
            "sample_size": len(evaluated_shadow),
            "confidence": "low",
            "basis": "mixed_shadow_and_live",
        })
    if possible_over_filtering:
        recommendation_notes.append({
            "type": "research_only",
            "message": "Watch for possible over-filtering: shadow winners are appearing outside live trades.",
            "why": "Missed winner count is higher than live trade count in the current sample.",
            "sample_size": len(missed_winners),
            "confidence": confidence,
            "basis": "shadow_vs_live_symbol_day_match",
        })
    if possible_under_filtering:
        recommendation_notes.append({
            "type": "research_only",
            "message": "Watch for possible under-filtering: bad live trades are a large share of live trades.",
            "why": "Bad live trade count is high relative to total live trades.",
            "sample_size": len(live_trades),
            "confidence": sample_confidence(len(live_trades)),
            "basis": "trade_history_csv",
        })
    if not recommendation_notes:
        recommendation_notes.append({
            "type": "research_only",
            "message": "No strong action signal yet. Continue collecting comparison data.",
            "why": "Current samples do not show a stable over-filtering or under-filtering pattern.",
            "sample_size": len(evaluated_shadow),
            "confidence": confidence,
            "basis": "mixed_shadow_and_live",
        })

    source_counts = Counter(str(s.get("source") or s.get("source_file") or "unknown") for s in shadow_rows)
    return {
        "generated_at": utc_now(),
        "updated_at": utc_now(),
        "mode": "shadow_vs_live_comparison",
        "status": "research_only",
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "live_trading_changed": False,
            "alpace_or_order_api_called": False,
        },
        "summary": {
            "live_trades_count": len(live_trades),
            "shadow_opportunities_count": len(shadow_rows),
            "evaluated_shadow_opportunities_count": len(evaluated_shadow),
            "matched_symbol_day_count": len(matched_shadow),
            "missed_winners_count": len(missed_winners),
            "missed_opportunity_rate": round((len(missed_winners) / max(1, len(shadow_rows))) * 100, 2),
            "bad_live_trade_count": len(bad_live),
            "bad_live_trade_rate": round((len(bad_live) / max(1, len(live_trades))) * 100, 2),
            "average_live_return_pct": live_avg,
            "average_shadow_return_pct": shadow_avg,
            "average_missed_winner_return_pct": missed_avg,
            "opportunity_cost_estimate_pct": opportunity_cost,
            "sample_label": sample_label(len(evaluated_shadow)),
            "confidence": confidence,
        },
        "missed_winners": sorted(missed_winners, key=lambda x: safe_float(x.get("return_pct"), -999) or -999, reverse=True)[:25],
        "bad_live_trades": sorted(bad_live, key=lambda x: safe_float(x.get("return_pct"), 0) or 0)[:25],
        "best_missed_setup_types": group_setup_stats(missed_winners)[:10],
        "worst_live_setup_types": sorted(group_setup_stats(bad_live), key=lambda x: safe_float(x.get("avg_return_pct"), 999) or 999)[:10],
        "filter_diagnostics": {
            "possible_over_filtering": possible_over_filtering,
            "possible_under_filtering": possible_under_filtering,
            "notes": [
                "Matching currently uses symbol + calendar day. This is intentionally conservative and may miss intraday nuance.",
                "Historical/backfill rows and real-time shadow rows are mixed in totals but sources are exposed for review.",
                "Do not change live thresholds from this output until sample sizes are meaningful and confirmed by live-shadow data.",
            ],
        },
        "recommendations": recommendation_notes,
        "source_breakdown": dict(source_counts.most_common()),
        "context": {
            "shadow_execution_present": bool(shadow_execution),
            "setup_outcomes_present": bool(setup_outcomes),
            "top_candidates_present": bool(top_candidates),
            "shadow_execution_summary": shadow_execution.get("summary", {}) if isinstance(shadow_execution, dict) else {},
            "setup_outcomes_total_rows": setup_outcomes.get("total_rows") if isinstance(setup_outcomes, dict) else None,
        },
        "data_quality": {
            "confidence": confidence,
            "sample_label": sample_label(len(evaluated_shadow)),
            "missing_sources": [w for w in warnings if w.startswith("missing:")],
            "warnings": warnings,
            "sample_sizes": {
                "live_trades": len(live_trades),
                "shadow_rows": len(shadow_rows),
                "evaluated_shadow_rows": len(evaluated_shadow),
                "missed_winners": len(missed_winners),
                "bad_live_trades": len(bad_live),
            },
        },
        "explanation": [
            "Research-only comparison between live trade history and shadow setup opportunities.",
            "The goal is decision-quality learning, not immediate live optimization.",
            "Recommendations are informational until enough evaluated live-shadow samples exist.",
        ],
    }


def main() -> Dict[str, Any]:
    warnings: List[str] = []

    live_raw, warning = read_csv(TRADE_HISTORY)
    if warning:
        warnings.append(warning)
    live_trades = [t for t in (normalize_live_trade(row) for row in live_raw) if t]

    shadow_rows, shadow_warnings = load_research_rows()
    warnings.extend(shadow_warnings)
    if not SHADOW_SETUPS.exists():
        warnings.append(f"missing: {SHADOW_SETUPS.relative_to(ROOT)}")

    shadow_execution, warning = read_json(SHADOW_EXECUTION, {})
    if warning:
        warnings.append(warning)
    setup_outcomes, warning = read_json(SETUP_OUTCOMES, {})
    if warning:
        warnings.append(warning)
    top_candidates, warning = read_json(TOP_CANDIDATES, [])
    if warning:
        warnings.append(warning)

    output = compare(live_trades, shadow_rows, shadow_execution, setup_outcomes, top_candidates, warnings)
    RESEARCH_OUT.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(json.dumps(output, indent=2, sort_keys=True))
    return output


if __name__ == "__main__":
    main()
