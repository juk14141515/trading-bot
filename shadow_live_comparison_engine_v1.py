"""Shadow vs Live Comparison Engine for Ponder Invest AI.

Research-only. Compares actual bot trade history against shadow setup
opportunities and writes a dashboard-friendly JSON report.

Safety guarantees:
- never imports bot.py
- never calls Alpaca
- never places orders
- never changes live trading, risk, scoring, or capital-allocation behavior
- handles missing/partial data without crashing cron jobs

v1.1 adds a live-shadow quality layer so historical/backfill rows can still teach
setup strength without dominating live decision diagnostics.
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

# Source weighting is intentionally conservative. Historical rows are useful for
# setup research, but they should not drive live threshold/allocator conclusions.
SOURCE_WEIGHTS = {
    "live_trade": 1.2,
    "daytime_top_candidates_shadow": 1.0,
    "shadow_execution": 1.0,
    "shadow_setup_logger": 1.0,
    "historical_backfill": 0.15,
}
DEFAULT_SOURCE_WEIGHT = 0.35
LIVE_SHADOW_SOURCES = {"daytime_top_candidates_shadow", "shadow_execution", "shadow_setup_logger"}
HISTORICAL_SOURCES = {"historical_backfill"}


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
    clean = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(clean)
        return parsed.isoformat(), parsed.date().isoformat()
    except Exception:
        return raw, raw[:10] if len(raw) >= 10 else raw


def normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def source_group(source: Any, source_file: Any = "") -> str:
    source_text = str(source or "").strip()
    file_text = str(source_file or "").strip()
    combined = f"{source_text} {file_text}".lower()
    if source_text in LIVE_SHADOW_SOURCES or "daytime_top_candidates_shadow" in combined:
        return "live_shadow"
    if source_text == "shadow_execution" or "shadow_execution" in combined:
        return "live_shadow"
    if source_text in HISTORICAL_SOURCES or "historical" in combined or "backfill" in combined:
        return "historical_backfill"
    return "other_shadow"


def source_weight(source: Any, source_file: Any = "") -> float:
    source_text = str(source or "").strip()
    group = source_group(source_text, source_file)
    if source_text in SOURCE_WEIGHTS:
        return SOURCE_WEIGHTS[source_text]
    if group == "live_shadow":
        return 1.0
    if group == "historical_backfill":
        return SOURCE_WEIGHTS["historical_backfill"]
    return DEFAULT_SOURCE_WEIGHT


def infer_return_pct(row: Dict[str, Any], preferred_keys: Iterable[str]) -> Optional[float]:
    for key in preferred_keys:
        value = safe_float(row.get(key))
        if value is not None:
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
        "source_group": "live_trade",
        "source_weight": SOURCE_WEIGHTS["live_trade"],
    }


def normalize_shadow_row(row: Dict[str, Any], source_file: str = "shadow_setups.csv") -> Optional[Dict[str, Any]]:
    symbol = normalize_symbol(first_value(row, ("symbol", "ticker", "asset")))
    if not symbol:
        return None
    timestamp, day = parse_timestamp(first_value(row, ("timestamp", "time", "date", "created_at")))
    setup_type = str(first_value(row, ("setup_type", "setup", "strategy", "label"), "unknown") or "unknown")
    outcome = str(first_value(row, ("outcome", "result", "status"), "pending") or "pending").lower()
    score = safe_float(first_value(row, ("score", "final_score", "confidence")), 0.0)
    return_pct = first_value(row, ("next_5d_return", "next_3d_return", "next_1d_return", "next_1h_return"), "")
    return_pct_num = safe_float(return_pct)
    source = str(first_value(row, ("source",), source_file) or source_file)
    group = source_group(source, source_file)
    weight = source_weight(source, source_file)
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
        "source": source,
        "source_file": source_file,
        "source_group": group,
        "source_weight": weight,
        "weighted_return_pct": safe_round((return_pct_num or 0) * weight) if return_pct_num is not None else None,
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


def weighted_avg(rows: Iterable[Dict[str, Any]], value_key: str = "return_pct") -> Optional[float]:
    weighted_total = 0.0
    weight_total = 0.0
    for row in rows:
        value = safe_float(row.get(value_key))
        weight = safe_float(row.get("source_weight"), DEFAULT_SOURCE_WEIGHT) or DEFAULT_SOURCE_WEIGHT
        if value is None:
            continue
        weighted_total += value * weight
        weight_total += weight
    if weight_total <= 0:
        return None
    return round(weighted_total / weight_total, 3)


def group_setup_stats(rows: List[Dict[str, Any]], key: str = "setup_type") -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "unknown")].append(row)
    out = []
    for name, items in grouped.items():
        returns = [safe_float(item.get("return_pct")) for item in items]
        winners = [item for item in items if item.get("is_winner")]
        source_counts = Counter(str(item.get("source_group") or "unknown") for item in items)
        out.append({
            key: name,
            "sample_size": len(items),
            "weighted_sample_size": round(sum(safe_float(item.get("source_weight"), DEFAULT_SOURCE_WEIGHT) or DEFAULT_SOURCE_WEIGHT for item in items), 2),
            "sample_label": sample_label(len(items)),
            "confidence": sample_confidence(len(items)),
            "winner_count": len(winners),
            "win_rate": round((len(winners) / max(1, len(items))) * 100, 2),
            "avg_return_pct": avg(returns),
            "weighted_avg_return_pct": weighted_avg(items),
            "source_mix": dict(source_counts.most_common()),
            "basis": sorted({str(item.get("source") or item.get("source_file") or "unknown") for item in items})[:5],
        })
    return sorted(out, key=lambda x: (safe_float(x.get("weighted_avg_return_pct"), -999) or -999), reverse=True)


def source_quality_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("source_group") or "unknown")].append(row)
    summary = {}
    for group, items in groups.items():
        evaluated = [item for item in items if str(item.get("outcome") or "pending") not in {"", "pending", "unknown"}]
        winners = [item for item in items if item.get("is_winner")]
        summary[group] = {
            "rows": len(items),
            "evaluated_rows": len(evaluated),
            "weighted_rows": round(sum(safe_float(item.get("source_weight"), DEFAULT_SOURCE_WEIGHT) or DEFAULT_SOURCE_WEIGHT for item in items), 2),
            "winner_count": len(winners),
            "avg_return_pct": avg([safe_float(item.get("return_pct")) for item in items]),
            "weighted_avg_return_pct": weighted_avg(items),
            "weight_used": SOURCE_WEIGHTS.get(group, DEFAULT_SOURCE_WEIGHT),
        }
    return summary


def compare(live_trades: List[Dict[str, Any]], shadow_rows: List[Dict[str, Any]], shadow_execution: Dict[str, Any], setup_outcomes: Dict[str, Any], top_candidates: Any, warnings: List[str]) -> Dict[str, Any]:
    live_keys = {(t.get("symbol"), t.get("day")) for t in live_trades if t.get("symbol") and t.get("day")}
    matched_shadow = [s for s in shadow_rows if (s.get("symbol"), s.get("day")) in live_keys]
    missed_winners = [s for s in shadow_rows if s.get("is_winner") and (s.get("symbol"), s.get("day")) not in live_keys]
    live_shadow_rows = [s for s in shadow_rows if s.get("source_group") == "live_shadow"]
    historical_rows = [s for s in shadow_rows if s.get("source_group") == "historical_backfill"]
    live_shadow_missed_winners = [s for s in missed_winners if s.get("source_group") == "live_shadow"]
    historical_missed_winners = [s for s in missed_winners if s.get("source_group") == "historical_backfill"]
    bad_live = [t for t in live_trades if t.get("is_bad_live_trade")]

    live_avg = avg([safe_float(t.get("return_pct")) for t in live_trades])
    shadow_avg = avg([safe_float(s.get("return_pct")) for s in shadow_rows if s.get("return_pct") is not None])
    weighted_shadow_avg = weighted_avg(shadow_rows)
    live_shadow_avg = avg([safe_float(s.get("return_pct")) for s in live_shadow_rows if s.get("return_pct") is not None])
    missed_avg = avg([safe_float(s.get("return_pct")) for s in missed_winners if s.get("return_pct") is not None])
    weighted_missed_avg = weighted_avg(missed_winners)
    opportunity_cost = None
    weighted_opportunity_cost = None
    if missed_avg is not None and live_avg is not None:
        opportunity_cost = round(missed_avg - live_avg, 3)
    if weighted_missed_avg is not None and live_avg is not None:
        weighted_opportunity_cost = round(weighted_missed_avg - live_avg, 3)

    evaluated_shadow = [s for s in shadow_rows if str(s.get("outcome") or "pending") not in {"", "pending", "unknown"}]
    evaluated_live_shadow = [s for s in live_shadow_rows if str(s.get("outcome") or "pending") not in {"", "pending", "unknown"}]
    confidence = sample_confidence(len(evaluated_live_shadow)) if evaluated_live_shadow else sample_confidence(len(evaluated_shadow))

    # Decision diagnostics prefer live-shadow rows. Historical rows only provide weak supporting evidence.
    possible_over_filtering = len(live_shadow_missed_winners) >= 3 and len(live_shadow_missed_winners) > len(live_trades)
    historical_over_filtering_support = len(historical_missed_winners) >= 100 and len(historical_missed_winners) > len(live_trades)
    possible_under_filtering = len(bad_live) >= 2 and len(bad_live) >= max(1, int(len(live_trades) * 0.4))

    recommendation_notes: List[Dict[str, Any]] = []
    if len(evaluated_live_shadow) < 100:
        recommendation_notes.append({
            "type": "research_only",
            "message": "Collect more live-shadow samples before changing live thresholds.",
            "why": "Live-shadow evaluated sample size is below 100, so historical data is supporting evidence only.",
            "sample_size": len(evaluated_live_shadow),
            "confidence": "low",
            "basis": "live_shadow_preferred",
        })
    if possible_over_filtering:
        recommendation_notes.append({
            "type": "research_only",
            "message": "Possible live over-filtering: current shadow winners are appearing outside live trades.",
            "why": "Live-shadow missed winner count is higher than live trade count in the current sample.",
            "sample_size": len(live_shadow_missed_winners),
            "confidence": confidence,
            "basis": "live_shadow_symbol_day_match",
        })
    elif historical_over_filtering_support:
        recommendation_notes.append({
            "type": "research_only",
            "message": "Historical data suggests over-filtering, but live-shadow confirmation is still needed.",
            "why": "Historical/backfill winners are down-weighted and should not directly change thresholds.",
            "sample_size": len(historical_missed_winners),
            "confidence": "low",
            "basis": "historical_backfill_downweighted",
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
            "message": "No strong action signal yet. Continue collecting live-shadow comparison data.",
            "why": "Current live-shadow samples do not show a stable over-filtering or under-filtering pattern.",
            "sample_size": len(evaluated_live_shadow),
            "confidence": confidence,
            "basis": "live_shadow_preferred",
        })

    source_counts = Counter(str(s.get("source") or s.get("source_file") or "unknown") for s in shadow_rows)
    source_group_counts = Counter(str(s.get("source_group") or "unknown") for s in shadow_rows)
    now = utc_now()
    return {
        "generated_at": now,
        "updated_at": now,
        "mode": "shadow_vs_live_comparison",
        "status": "research_only",
        "version": "shadow_live_comparison_engine_v1.1_live_quality_weighting",
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
            "alpaca_or_order_api_called": False,
        },
        "summary": {
            "live_trades_count": len(live_trades),
            "shadow_opportunities_count": len(shadow_rows),
            "live_shadow_opportunities_count": len(live_shadow_rows),
            "historical_backfill_opportunities_count": len(historical_rows),
            "evaluated_shadow_opportunities_count": len(evaluated_shadow),
            "evaluated_live_shadow_opportunities_count": len(evaluated_live_shadow),
            "matched_symbol_day_count": len(matched_shadow),
            "missed_winners_count": len(missed_winners),
            "live_shadow_missed_winners_count": len(live_shadow_missed_winners),
            "historical_missed_winners_count": len(historical_missed_winners),
            "missed_opportunity_rate": round((len(missed_winners) / max(1, len(shadow_rows))) * 100, 2),
            "live_shadow_missed_opportunity_rate": round((len(live_shadow_missed_winners) / max(1, len(live_shadow_rows))) * 100, 2),
            "bad_live_trade_count": len(bad_live),
            "bad_live_trade_rate": round((len(bad_live) / max(1, len(live_trades))) * 100, 2),
            "average_live_return_pct": live_avg,
            "average_shadow_return_pct": shadow_avg,
            "weighted_average_shadow_return_pct": weighted_shadow_avg,
            "average_live_shadow_return_pct": live_shadow_avg,
            "average_missed_winner_return_pct": missed_avg,
            "weighted_average_missed_winner_return_pct": weighted_missed_avg,
            "opportunity_cost_estimate_pct": opportunity_cost,
            "weighted_opportunity_cost_estimate_pct": weighted_opportunity_cost,
            "sample_label": sample_label(len(evaluated_live_shadow)) if evaluated_live_shadow else sample_label(len(evaluated_shadow)),
            "confidence": confidence,
        },
        "live_shadow_missed_winners": sorted(live_shadow_missed_winners, key=lambda x: safe_float(x.get("return_pct"), -999) or -999, reverse=True)[:25],
        "missed_winners": sorted(missed_winners, key=lambda x: safe_float(x.get("return_pct"), -999) or -999, reverse=True)[:25],
        "bad_live_trades": sorted(bad_live, key=lambda x: safe_float(x.get("return_pct"), 0) or 0)[:25],
        "best_live_shadow_setup_types": group_setup_stats(live_shadow_missed_winners)[:10],
        "best_missed_setup_types": group_setup_stats(missed_winners)[:10],
        "worst_live_setup_types": sorted(group_setup_stats(bad_live), key=lambda x: safe_float(x.get("avg_return_pct"), 999) or 999)[:10],
        "filter_diagnostics": {
            "possible_over_filtering": possible_over_filtering,
            "historical_over_filtering_support": historical_over_filtering_support,
            "possible_under_filtering": possible_under_filtering,
            "notes": [
                "Matching currently uses symbol + calendar day. This is intentionally conservative and may miss intraday nuance.",
                "Live-shadow rows are now preferred for diagnostics; historical/backfill rows are down-weighted supporting evidence.",
                "Do not change live thresholds from historical rows alone. Require live-shadow confirmation first.",
            ],
        },
        "source_weighting": {
            "policy": "live_shadow_preferred_historical_downweighted",
            "weights": SOURCE_WEIGHTS,
            "default_weight": DEFAULT_SOURCE_WEIGHT,
            "source_groups": dict(source_group_counts.most_common()),
            "quality_summary": source_quality_summary(shadow_rows),
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
            "sample_label": sample_label(len(evaluated_live_shadow)) if evaluated_live_shadow else sample_label(len(evaluated_shadow)),
            "missing_sources": [w for w in warnings if w.startswith("missing:")],
            "warnings": warnings,
            "sample_sizes": {
                "live_trades": len(live_trades),
                "shadow_rows": len(shadow_rows),
                "live_shadow_rows": len(live_shadow_rows),
                "historical_backfill_rows": len(historical_rows),
                "evaluated_shadow_rows": len(evaluated_shadow),
                "evaluated_live_shadow_rows": len(evaluated_live_shadow),
                "missed_winners": len(missed_winners),
                "live_shadow_missed_winners": len(live_shadow_missed_winners),
                "bad_live_trades": len(bad_live),
            },
        },
        "explanation": [
            "Research-only comparison between live trade history and shadow setup opportunities.",
            "The goal is decision-quality learning, not immediate live optimization.",
            "Live-shadow samples are preferred; historical/backfill samples are down-weighted and informational.",
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
