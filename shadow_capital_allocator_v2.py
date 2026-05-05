"""Research-only Shadow Capital Allocator v2.1.

Reads existing research JSON/CSV and writes one dashboard JSON file.
No broker imports, no live execution, no order APIs, no live-system changes.

Main safety fix:
- historical/backfill missed winners are learning-only and receive $0 allocation
- only current/recent shadow candidates can receive research-only shadow allocation
- crypto gets a separate high-risk bucket instead of core capital
"""

from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
RESEARCH_OUT = ROOT / "static" / "research"
OUT_FILE = RESEARCH_OUT / "shadow_capital_allocator_v2_latest.json"

CAPITAL = RESEARCH_OUT / "capital_intelligence_latest.json"
CAPITAL_HISTORY = RESEARCH_OUT / "capital_history.csv"
SHADOW_LIVE = RESEARCH_OUT / "shadow_live_comparison_latest.json"
SHADOW_EXECUTION = RESEARCH_OUT / "shadow_execution_latest.json"
SETUP_OUTCOMES = RESEARCH_OUT / "setup_outcomes_latest.json"
ROTATION = RESEARCH_OUT / "rotation_engine_latest.json"
BOT_STATUS = ROOT / "bot_status.json"
TRADE_HISTORY = ROOT / "trade_history.csv"

PROFIT_POLICY = "reinvest_until_edge_proven"
DEFAULT_TAX_RATE = float(os.getenv("PONDER_ALLOCATOR_TAX_RATE", "0.25"))
DEFAULT_STARTING_CAPITAL = float(os.getenv("PONDER_ALLOCATOR_STARTING_CAPITAL", "500"))
CURRENT_CANDIDATE_MAX_AGE_HOURS = float(os.getenv("PONDER_ALLOCATOR_CURRENT_HOURS", "36"))
MAX_CURRENT_TOTAL_ALLOCATION_PCT = float(os.getenv("PONDER_ALLOCATOR_MAX_TOTAL_PCT", "0.25"))

TIER_RULES = {
    "micro": {
        "max_positions": 1,
        "core_pct": 0.40,
        "crypto_pct": 0.08,
        "ipo_pct": 0.12,
        "day_pct": 0.08,
        "reserve_pct": 0.28,
        "max_core_pct": 0.18,
        "max_crypto_pct": 0.08,
        "max_ipo_pct": 0.10,
        "max_day_pct": 0.06,
        "rotation_hurdle": 25,
    },
    "small": {
        "max_positions": 2,
        "core_pct": 0.45,
        "crypto_pct": 0.08,
        "ipo_pct": 0.12,
        "day_pct": 0.08,
        "reserve_pct": 0.24,
        "max_core_pct": 0.16,
        "max_crypto_pct": 0.07,
        "max_ipo_pct": 0.09,
        "max_day_pct": 0.05,
        "rotation_hurdle": 22,
    },
    "starter": {
        "max_positions": 4,
        "core_pct": 0.50,
        "crypto_pct": 0.07,
        "ipo_pct": 0.10,
        "day_pct": 0.07,
        "reserve_pct": 0.20,
        "max_core_pct": 0.14,
        "max_crypto_pct": 0.06,
        "max_ipo_pct": 0.08,
        "max_day_pct": 0.05,
        "rotation_hurdle": 18,
    },
    "growth": {
        "max_positions": 5,
        "core_pct": 0.55,
        "crypto_pct": 0.06,
        "ipo_pct": 0.09,
        "day_pct": 0.06,
        "reserve_pct": 0.18,
        "max_core_pct": 0.12,
        "max_crypto_pct": 0.05,
        "max_ipo_pct": 0.07,
        "max_day_pct": 0.04,
        "rotation_hurdle": 15,
    },
}

LEARNING_ONLY_MARKERS = (
    "historical_backfill",
    "crypto_setups.csv",
    "gap_setups.csv",
    "ipo_setups.csv",
    "daytrade_setups.csv",
    "smallcap_setups.csv",
    "largecap",
    "earnings",
    "etf_setups",
)
CURRENT_SOURCES = {"shadow_execution", "daytime_top_candidates_shadow", "top_candidates", "scanner_current"}


def now_dt() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_dt().isoformat(timespec="seconds")


def fnum(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value in (None, "", "None", "nan", "NaN"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def rnum(value: Any, digits: int = 2) -> Optional[float]:
    number = fnum(value)
    return None if number is None else round(number, digits)


def read_json(path: Path, default: Any) -> Tuple[Any, Optional[str]]:
    if not path.exists():
        return default, f"missing: {path.name}"
    try:
        return json.loads(path.read_text()), None
    except Exception as exc:
        return default, f"error reading {path.name}: {type(exc).__name__}: {exc}"


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], Optional[str]]:
    if not path.exists():
        return [], f"missing: {path.name}"
    try:
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle)), None
    except Exception as exc:
        return [], f"error reading {path.name}: {type(exc).__name__}: {exc}"


def first(row: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", "None", "nan", "NaN"):
            return value
    return default


def parse_ts(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    clean = raw.replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            if fmt:
                parsed = datetime.strptime(raw[:19], fmt).replace(tzinfo=timezone.utc)
            else:
                parsed = datetime.fromisoformat(clean)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def tier_for(equity: float) -> str:
    if equity < 1000:
        return "micro"
    if equity < 3000:
        return "small"
    if equity < 10000:
        return "starter"
    return "growth"


def stable_equity(rows: List[Dict[str, str]], current: float) -> float:
    values: List[Tuple[datetime, float]] = []
    for row in rows:
        ts = parse_ts(row.get("timestamp"))
        equity = fnum(first(row, ("equity", "portfolio_value", "account_equity")))
        if ts and equity and equity > 0:
            values.append((ts, equity))
    if not values:
        return round(current, 2)
    recent = [value for _, value in sorted(values, key=lambda item: item[0])[-20:]]
    return round(sum(recent) / len(recent), 2) if recent else round(current, 2)


def realized_profit(capital: Dict[str, Any], rows: List[Dict[str, str]]) -> float:
    for key in ("realized_pl", "realized_profit", "closed_pl", "all_time_realized_pl"):
        value = fnum(capital.get(key))
        if value is not None:
            return round(value, 2)

    total = 0.0
    found = False
    for row in rows:
        value = fnum(first(row, ("realized_pl", "pnl", "pl", "profit_loss", "net_pl")))
        if value is not None:
            total += value
            found = True

    if found:
        return round(total, 2)

    equity = fnum(first(capital, ("equity", "portfolio_value")), 0) or 0
    return round(max(0, equity - DEFAULT_STARTING_CAPITAL), 2)


def build_buckets(equity: float, cash: float, deployable: float, tier: str, realized: float) -> Dict[str, Dict[str, Any]]:
    rules = TIER_RULES[tier]
    tax = round(max(0, realized) * DEFAULT_TAX_RATE, 2)
    allocatable = max(0.0, min(cash, deployable) - tax)

    specs = {
        "core_capital": (rules["core_pct"], "Normal higher-quality core opportunities."),
        "crypto_capital": (rules["crypto_pct"], "High-risk crypto momentum only; separate from core."),
        "ipo_capital": (rules["ipo_pct"], "High-risk IPO/catalyst/hype only."),
        "day_trade_capital": (rules["day_pct"], "High-frequency learning/day-trade candidates; shadow-first."),
    }

    output: Dict[str, Dict[str, Any]] = {}
    for name, (pct, purpose) in specs.items():
        target = round(equity * pct, 2)
        output[name] = {
            "target_dollars": target,
            "available_dollars": round(min(allocatable, target), 2),
            "deployable": True,
            "purpose": purpose,
        }

    reserve = round(equity * rules["reserve_pct"], 2)
    profit_reserve = round(max(0, realized) * 0.10, 2)
    output.update(
        {
            "reserve_cash": {
                "target_dollars": reserve,
                "available_dollars": reserve,
                "deployable": False,
                "purpose": "Capital protection buffer.",
            },
            "pending_cash": {
                "target_dollars": 0.0,
                "available_dollars": 0.0,
                "deployable": False,
                "purpose": "New deposits staged before gradual deployment.",
            },
            "profit_reserve": {
                "target_dollars": profit_reserve,
                "available_dollars": profit_reserve,
                "deployable": False,
                "purpose": "Profit reserve tracked until edge is proven.",
            },
            "tax_reserve": {
                "target_dollars": tax,
                "available_dollars": tax,
                "deployable": False,
                "purpose": "Estimated tax set-aside; never deployable.",
            },
        }
    )
    return output


def bucket_for(setup: str, source: str = "") -> str:
    text = f"{setup} {source}".lower()
    if any(token in text for token in ("crypto", "doge", "btc", "eth")):
        return "crypto_capital"
    if "ipo" in text:
        return "ipo_capital"
    if any(token in text for token in ("day", "intraday", "scalp")):
        return "day_trade_capital"
    return "core_capital"


def max_pct(bucket: str, rules: Dict[str, Any]) -> float:
    if bucket == "crypto_capital":
        return rules["max_crypto_pct"]
    if bucket == "ipo_capital":
        return rules["max_ipo_pct"]
    if bucket == "day_trade_capital":
        return rules["max_day_pct"]
    return rules["max_core_pct"]


def setup_stats_map(setup_outcomes: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(setup_outcomes, dict):
        return {}
    setups = setup_outcomes.get("setups") or setup_outcomes.get("by_setup") or {}
    return setups if isinstance(setups, dict) else {}


def score_row(row: Dict[str, Any], setup_stats: Dict[str, Any]) -> Dict[str, Any]:
    setup = str(first(row, ("setup_type", "setup"), "unknown"))
    score = fnum(first(row, ("score", "edge_score", "rotation_score")), 0) or 0
    return_pct = fnum(first(row, ("return_pct", "next_5d_return", "avg_5d", "avg_return_pct")), 0) or 0

    stats = setup_stats.get(setup, {}) if isinstance(setup_stats, dict) else {}
    avg = fnum(first(stats, ("avg_5d", "avg_return_pct", "avg_5d_return")), 0) or 0
    win_rate = fnum(first(stats, ("win_rate",)), 0) or 0
    sample_size = int(fnum(first(stats, ("count", "sample_size", "total")), 0) or 0)

    sample_bonus = 15 if sample_size >= 300 else 8 if sample_size >= 100 else 2 if sample_size >= 25 else 0
    quality = (score * 0.45) + (return_pct * 3.0) + (avg * 2.0) + (win_rate * 0.2) + sample_bonus

    return {
        "quality_score": round(quality, 2),
        "raw_score": round(score, 2),
        "expected_return_pct": round(return_pct or avg, 3),
        "sample_size": sample_size,
        "sample_label": "meaningful_signal" if sample_size >= 300 else "early_signal" if sample_size >= 100 else "informational_only",
        "confidence": "high" if sample_size >= 300 else "medium" if sample_size >= 100 else "low",
    }


def eligibility(row: Dict[str, Any], source: str) -> Dict[str, Any]:
    raw_source = str(first(row, ("source", "source_file", "raw_source"), "") or "")
    source_file = str(row.get("source_file", "") or "")
    ts = parse_ts(first(row, ("timestamp", "created_at", "time", "date", "day")))
    age = None if not ts else max(0.0, (now_dt() - ts).total_seconds() / 3600)
    text = f"{source} {raw_source} {source_file}".lower()

    if any(marker in text for marker in LEARNING_ONLY_MARKERS):
        status = "learning_only"
        reason = "Historical/backfill rows teach setup strength but are not current deployable candidates."
        current = False
    elif source in CURRENT_SOURCES and (age is None or age <= CURRENT_CANDIDATE_MAX_AGE_HOURS):
        status = "shadow_allocatable"
        reason = "Current/recent shadow candidate eligible for research-only allocation."
        current = True
    elif source == "missed_winner":
        status = "learning_only"
        reason = "Missed winner is used for opportunity-cost learning unless it is current."
        current = False
    else:
        status = "watch_only"
        reason = "Candidate source/timestamp is not strong enough for allocation."
        current = False

    return {
        "allocation_eligibility": status,
        "eligibility_reason": reason,
        "is_current_candidate": current,
        "source_timestamp": ts.isoformat(timespec="seconds") if ts else None,
        "source_age_hours": rnum(age, 2),
    }


def collect_opportunities(shadow_execution: Dict[str, Any], comparison: Dict[str, Any], setup_outcomes: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Tuple[str, Dict[str, Any]]] = []

    for row in shadow_execution.get("top_shadow_trades", []) if isinstance(shadow_execution, dict) else []:
        if isinstance(row, dict):
            rows.append(("shadow_execution", dict(row)))

    for row in comparison.get("missed_winners", []) if isinstance(comparison, dict) else []:
        if isinstance(row, dict):
            rows.append(("missed_winner", dict(row)))

    stats = setup_stats_map(setup_outcomes)
    output: List[Dict[str, Any]] = []
    seen = set()

    for source, row in rows:
        symbol = str(first(row, ("symbol", "ticker"), "UNKNOWN") or "UNKNOWN").upper()
        setup = str(first(row, ("setup_type", "setup"), "unknown") or "unknown")
        key = (symbol, setup, source, str(first(row, ("timestamp", "day", "date"), "")))
        if key in seen:
            continue
        seen.add(key)

        metrics = score_row(row, stats)
        output.append(
            {
                "symbol": symbol,
                "setup_type": setup,
                "bucket": bucket_for(setup, f"{source} {row.get('source', '')} {row.get('source_file', '')}"),
                "opportunity_source": source,
                "raw_source": row.get("source"),
                "source_file": row.get("source_file"),
                "why": first(row, ("why", "reason", "decision_reason", "summary"), "Research opportunity from shadow pipeline."),
                **metrics,
                **eligibility(row, source),
            }
        )

    return sorted(output, key=lambda item: item["quality_score"], reverse=True)


def losing_streak(rows: List[Dict[str, str]]) -> int:
    normalized = []
    for row in rows:
        ts = parse_ts(first(row, ("exit_time", "closed_at", "timestamp", "time", "date", "entry_time"))) or datetime.min.replace(tzinfo=timezone.utc)
        ret = fnum(first(row, ("return_pct", "pnl_pct", "pl_pct", "profit_pct")))
        pnl = fnum(first(row, ("realized_pl", "pnl", "pl", "profit_loss", "net_pl")))
        is_loss = (ret is not None and ret < 0) or (ret is None and pnl is not None and pnl < 0)
        normalized.append((ts, is_loss))

    streak = 0
    for _, is_loss in sorted(normalized, key=lambda item: item[0], reverse=True):
        if is_loss:
            streak += 1
        else:
            break
    return streak


def risk_clusters(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    current = [item for item in opportunities if item.get("allocation_eligibility") == "shadow_allocatable"] or opportunities[:10]
    clusters = []

    for cluster_type, counts in (
        ("bucket", Counter(item.get("bucket", "unknown") for item in current[:10])),
        ("setup_type", Counter(item.get("setup_type", "unknown") for item in current[:10])),
    ):
        for name, count in counts.items():
            if count >= 3:
                clusters.append(
                    {
                        "cluster_type": cluster_type,
                        "name": name,
                        "count": count,
                        "warning": "Multiple current/top opportunities share the same risk.",
                    }
                )

    return clusters


def allocate(opportunities: List[Dict[str, Any]], buckets: Dict[str, Dict[str, Any]], equity: float, tier: str, streak: int) -> List[Dict[str, Any]]:
    rules = TIER_RULES[tier]
    remaining = {name: fnum(data.get("available_dollars"), 0) or 0 for name, data in buckets.items()}
    total_cap = equity * MAX_CURRENT_TOTAL_ALLOCATION_PCT
    total_used = 0.0
    max_positions = int(rules["max_positions"])
    funded = 0

    current_candidates = [item for item in opportunities if item.get("allocation_eligibility") == "shadow_allocatable"]
    clusters = risk_clusters(current_candidates)
    cluster_penalty = 0.5 if clusters else 1.0
    decisions = []

    for opportunity in opportunities[:25]:
        bucket = opportunity.get("bucket", "core_capital")
        available = remaining.get(bucket, 0)
        suggested = 0.0
        reasons = [opportunity.get("eligibility_reason", "")]

        if opportunity.get("allocation_eligibility") != "shadow_allocatable":
            decision = "research_learning_only"
            reasons.append("Learning-only opportunities do not consume capital buckets.")
        else:
            confidence = opportunity.get("confidence")
            mult = (1.0 if confidence == "high" else 0.6 if confidence == "medium" else 0.25) * cluster_penalty
            pct = max_pct(bucket, rules)

            if streak >= 3:
                pct *= 0.5
                mult *= 0.5

            suggested = min(round(equity * pct * mult, 2), available, max(0, total_cap - total_used))

            if funded >= max_positions:
                decision = "watch_only_max_positions_reached"
                suggested = 0
            elif available <= 0:
                decision = "watch_only_no_bucket_cash"
                suggested = 0
            elif total_used >= total_cap:
                decision = "watch_only_total_cap_reached"
                suggested = 0
            elif confidence == "low":
                decision = "shadow_watch_low_confidence"
                suggested = round(min(suggested, equity * 0.03), 2)
            elif (fnum(opportunity.get("quality_score"), 0) or 0) < 50:
                decision = "skip_low_quality"
                suggested = 0
            else:
                decision = "shadow_allocate"

            reasons.append("Current candidate evaluated under research-only allocation rules.")

        if suggested > 0 and decision in {"shadow_allocate", "shadow_watch_low_confidence"}:
            remaining[bucket] = round(max(0, remaining[bucket] - suggested), 2)
            total_used += suggested
            funded += 1

        if bucket == "crypto_capital":
            reasons.append("Crypto uses separate high-risk bucket; not core capital.")
        if bucket == "ipo_capital":
            reasons.append("IPO/catalyst uses separate high-risk bucket.")
        if bucket == "day_trade_capital":
            reasons.append("Day-trade bucket remains shadow-first and PDT-aware.")
        if cluster_penalty < 1 and opportunity.get("allocation_eligibility") == "shadow_allocatable":
            reasons.append("Cluster risk detected: allocation reduced.")

        decisions.append(
            {
                **opportunity,
                "decision": decision,
                "suggested_allocation_pct": round((suggested / equity) * 100, 2) if equity else 0,
                "suggested_dollar_amount": round(suggested, 2),
                "was_capital_available": available > 0,
                "would_this_have_been_taken": suggested > 0 and decision in {"shadow_allocate", "shadow_watch_low_confidence"},
                "why": " ".join(reason for reason in reasons if reason),
                "source": opportunity.get("opportunity_source"),
                "automation_allowed": False,
            }
        )

    return decisions


def learning_setups(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for opportunity in opportunities:
        if opportunity.get("allocation_eligibility") == "learning_only":
            grouped[opportunity.get("setup_type", "unknown")].append(opportunity)

    rows = []
    for setup, items in grouped.items():
        avg_return = sum((fnum(item.get("expected_return_pct"), 0) or 0) for item in items) / max(1, len(items))
        avg_quality = sum((fnum(item.get("quality_score"), 0) or 0) for item in items) / max(1, len(items))
        rows.append(
            {
                "setup_type": setup,
                "bucket": bucket_for(setup),
                "sample_count": len(items),
                "avg_expected_return_pct": rnum(avg_return, 3),
                "avg_quality_score": rnum(avg_quality, 2),
                "best_symbol": items[0].get("symbol") if items else None,
                "status": "learning_only_not_deployable",
            }
        )

    return sorted(rows, key=lambda item: fnum(item.get("avg_quality_score"), 0) or 0, reverse=True)


def small_account_simulation() -> Dict[str, Any]:
    output = {}

    for amount in (500, 1000, 3000):
        tier = tier_for(float(amount))
        rules = TIER_RULES[tier]
        output[str(amount)] = {
            "simulated_equity": amount,
            "tier": tier,
            "max_positions": rules["max_positions"],
            "max_core_trade_dollars": round(amount * rules["max_core_pct"], 2),
            "max_crypto_trade_dollars": round(amount * rules["max_crypto_pct"], 2),
            "max_ipo_trade_dollars": round(amount * rules["max_ipo_pct"], 2),
            "max_day_trade_dollars": round(amount * rules["max_day_pct"], 2),
            "reserve_cash": round(amount * rules["reserve_pct"], 2),
            "note": "Future real-cash deployment should use small-account rules, not paper-account scale.",
        }

    return output


def edge_gate(comparison: Dict[str, Any]) -> Dict[str, Any]:
    summary = comparison.get("summary", {}) if isinstance(comparison, dict) else {}
    sample = int(fnum(first(summary, ("evaluated_shadow_opportunities_count", "shadow_opportunities_count")), 0) or 0)
    confidence = str(first(summary, ("confidence",), "low") or "low").lower()
    avg_shadow = fnum(summary.get("average_shadow_return_pct"), 0) or 0
    bad_rate = fnum(summary.get("bad_live_trade_rate"), 100) or 100
    proven = sample >= 300 and confidence == "high" and avg_shadow > 0 and bad_rate < 35

    return {
        "edge_proven": proven,
        "withdrawal_enabled": bool(proven),
        "reason": "Withdrawals stay disabled until sample size, confidence, returns, and risk are proven." if not proven else "Edge gate passed; manual review still required.",
        "requirements": {
            "sample_size_min": 300,
            "confidence_required": "high",
            "average_shadow_return_positive": True,
            "bad_live_trade_rate_below_pct": 35,
        },
        "current": {
            "sample_size": sample,
            "confidence": confidence,
            "average_shadow_return_pct": rnum(avg_shadow, 3),
            "bad_live_trade_rate": rnum(bad_rate, 2),
        },
    }


def rotation_decisions(rotation: Dict[str, Any], equity: float, tier: str) -> List[Dict[str, Any]]:
    rules = TIER_RULES[tier]
    output = []

    for row in rotation.get("rotation_suggestions", [])[:20] if isinstance(rotation, dict) else []:
        if not isinstance(row, dict):
            continue

        score = fnum(row.get("rotation_score"), 0) or 0
        edge = fnum(row.get("expected_edge"), 0) or 0
        confidence = str(row.get("confidence", "low")).lower()

        if confidence == "high" and (score >= 70 or edge >= rules["rotation_hurdle"]):
            decision = "shadow_only_partial_rotate"
            pct = min(0.25, rules["max_core_pct"])
            why = "Meaningful rotation edge, but automation remains disabled."
        elif confidence in {"medium", "high"} and (score >= 60 or edge >= rules["rotation_hurdle"] * 0.7):
            decision = "watch_rotation"
            pct = 0.0
            why = "Potential rotation, but edge/confidence is not strong enough."
        else:
            decision = "hold_current_position"
            pct = 0.0
            why = "Rotation hurdle not met. Avoid churn."

        output.append(
            {
                "sell_symbol": row.get("sell_symbol"),
                "buy_symbol": row.get("buy_symbol"),
                "rotation_score": rnum(score, 2),
                "expected_edge": rnum(edge, 2),
                "confidence": confidence,
                "rotation_decision": decision,
                "capital_to_move_pct": round(pct * 100, 2),
                "capital_to_move_dollars": round(equity * pct, 2),
                "why": why,
                "automation_allowed": False,
            }
        )

    return output


def main() -> Dict[str, Any]:
    warnings: List[str] = []

    def load_json(path: Path, default: Any) -> Any:
        data, warning = read_json(path, default)
        if warning:
            warnings.append(warning)
        return data

    def load_csv(path: Path) -> List[Dict[str, str]]:
        data, warning = read_csv(path)
        if warning:
            warnings.append(warning)
        return data

    capital = load_json(CAPITAL, {})
    comparison = load_json(SHADOW_LIVE, {})
    shadow_execution = load_json(SHADOW_EXECUTION, {})
    setup_outcomes = load_json(SETUP_OUTCOMES, {})
    rotation = load_json(ROTATION, {})
    bot_status = load_json(BOT_STATUS, {})
    capital_history = load_csv(CAPITAL_HISTORY)
    trade_history = load_csv(TRADE_HISTORY)

    equity = fnum(first(capital, ("equity", "portfolio_value", "account_equity")), DEFAULT_STARTING_CAPITAL) or DEFAULT_STARTING_CAPITAL
    cash = fnum(first(capital, ("cash", "buying_power")), equity) or equity
    deployable = fnum(capital.get("deployable_cash"), max(0, cash * 0.7)) or 0
    stable = stable_equity(capital_history, equity)
    tier = tier_for(stable)
    rules = TIER_RULES[tier]
    realized = realized_profit(capital, trade_history)
    buckets = build_buckets(equity, cash, deployable, tier, realized)
    opportunities = collect_opportunities(shadow_execution, comparison, setup_outcomes)
    streak = losing_streak(trade_history)
    decisions = allocate(opportunities, buckets, equity, tier, streak)

    current = [item for item in decisions if item.get("allocation_eligibility") == "shadow_allocatable"]
    learning = [item for item in decisions if item.get("allocation_eligibility") == "learning_only"]
    clusters = risk_clusters(opportunities)
    gate = edge_gate(comparison)
    suggested = sum(fnum(item.get("suggested_dollar_amount"), 0) or 0 for item in current)
    top = next((item for item in current if item.get("would_this_have_been_taken")), current[0] if current else {})

    output = {
        "generated_at": now_iso(),
        "updated_at": now_iso(),
        "version": "shadow_capital_allocator_v2.1",
        "status": "research_only",
        "mode": "shadow_allocation_only",
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "live_trading_changed": False,
            "automation_allowed": False,
            "note": "Dashboard/research output only. No execution hooks.",
        },
        "policy": {
            "profit_policy": PROFIT_POLICY,
            "withdrawal_policy": "disabled_until_edge_proven_then_manual_review",
            "tax_reserve_enabled": True,
            "estimated_tax_rate": DEFAULT_TAX_RATE,
            "deposits_policy": "new_cash_goes_to_pending_bucket_before_gradual_deployment",
            "tier_policy": "stable_equity_with_buffers_not_instant_balance",
            "rotation_policy": "allocator_is_gatekeeper; shadow-only until proven",
            "historical_rows_policy": "learning_only_not_allocatable",
            "max_current_total_allocation_pct": MAX_CURRENT_TOTAL_ALLOCATION_PCT,
        },
        "account": {
            "equity": rnum(equity),
            "cash": rnum(cash),
            "deployable_cash_reported": rnum(deployable),
            "stable_equity": rnum(stable),
            "tier": tier,
            "tier_rules": rules,
            "realized_profit_estimate": rnum(realized),
            "recent_losing_streak": streak,
        },
        "capital_buckets": buckets,
        "summary": {
            "opportunities_seen": len(opportunities),
            "allocation_decisions": len(decisions),
            "current_candidates": len(current),
            "historical_learning_opportunities": len(learning),
            "shadow_allocations": sum(1 for item in current if item.get("would_this_have_been_taken")),
            "suggested_total_dollars": round(suggested, 2),
            "suggested_total_pct": round((suggested / equity) * 100, 2) if equity else 0,
            "top_decision": top,
            "risk_clusters": len(clusters),
            "edge_proven": gate.get("edge_proven"),
            "withdrawal_enabled": gate.get("withdrawal_enabled"),
        },
        "allocation_decisions": decisions,
        "current_allocation_decisions": current,
        "historical_learning_opportunities": learning[:25],
        "learning_only_top_setups": learning_setups(opportunities)[:15],
        "small_account_simulation": small_account_simulation(),
        "rotation_decisions": rotation_decisions(rotation, equity, tier),
        "risk_controls": {
            "risk_clusters": clusters,
            "losing_streak_protection_active": streak >= 3,
            "small_account_churn_control": {
                "max_positions": rules["max_positions"],
                "rotation_hurdle": rules["rotation_hurdle"],
                "max_one_rotation_per_day_recommended": tier in {"micro", "small", "starter"},
            },
            "pdt_day_trade_warning": "Day-trade bucket is shadow-first and should remain PDT-aware for accounts under $25k.",
        },
        "edge_validation_gate": gate,
        "profit_and_withdrawal_plan": {
            "current_policy": PROFIT_POLICY,
            "reinvest_most_or_all": True,
            "withdrawals_now": "not_recommended",
            "tax_reserve_dollars": buckets["tax_reserve"]["target_dollars"],
            "profit_reserve_dollars": buckets["profit_reserve"]["target_dollars"],
            "manual_review_required_before_any_withdrawal": True,
            "notes": [
                "Only realized profits should ever become withdrawable.",
                "Tax reserve is tracked even while profits are reinvested.",
                "Do not withdraw if it breaks tier buffers or reduces active-protection rules.",
            ],
        },
        "data_quality": {
            "warnings": warnings,
            "missing_sources": [item for item in warnings if str(item).startswith("missing:")],
            "inputs_present": {
                "capital_intelligence": bool(capital),
                "shadow_live_comparison": bool(comparison),
                "shadow_execution": bool(shadow_execution),
                "setup_outcomes": bool(setup_outcomes),
                "rotation_engine": bool(rotation),
                "trade_history_rows": len(trade_history),
                "capital_history_rows": len(capital_history),
            },
        },
        "explanation": [
            "Allocator v2.1 separates current allocatable candidates from historical learning rows.",
            "Historical/backfill missed winners improve setup intelligence but receive $0 allocation.",
            "Crypto, IPO, day-trade, core, reserve, pending, profit, and tax capital are separated.",
            "Rotation decisions are evaluated but never automated here.",
        ],
    }

    RESEARCH_OUT.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(json.dumps(output, indent=2, sort_keys=True))
    return output


if __name__ == "__main__":
    main()
