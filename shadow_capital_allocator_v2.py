"""Shadow Capital Allocator v2 for Ponder Invest AI.

Research-only capital allocation intelligence.

This module answers:
- What deserves scarce capital?
- Which bucket should fund it: core, IPO, day-trade, reserve, pending, tax?
- Should capital rotate, wait, or stay protected?
- Are profits reinvestable, reserved, or withdrawable later?

Safety guarantees:
- never imports bot.py
- never calls Alpaca
- never places orders
- never changes risk_manager, live sizing, capital allocation, or order behavior
- writes dashboard-ready JSON only
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
RESEARCH_DATA = ROOT / "research_data"
OUT_FILE = RESEARCH_OUT / "shadow_capital_allocator_v2_latest.json"

CAPITAL = RESEARCH_OUT / "capital_intelligence_latest.json"
CAPITAL_HISTORY = RESEARCH_OUT / "capital_history.csv"
SHADOW_LIVE = RESEARCH_OUT / "shadow_live_comparison_latest.json"
SHADOW_EXECUTION = RESEARCH_OUT / "shadow_execution_latest.json"
SETUP_OUTCOMES = RESEARCH_OUT / "setup_outcomes_latest.json"
ROTATION = RESEARCH_OUT / "rotation_engine_latest.json"
BOT_STATUS = ROOT / "bot_status.json"
TRADE_HISTORY = ROOT / "trade_history.csv"

# User policy: reinvest first, prove edge, then withdraw later.
PROFIT_POLICY = "reinvest_until_edge_proven"
DEFAULT_TAX_RATE = float(os.getenv("PONDER_ALLOCATOR_TAX_RATE", "0.25"))
DEFAULT_STARTING_CAPITAL = float(os.getenv("PONDER_ALLOCATOR_STARTING_CAPITAL", "500"))

TIER_RULES = {
    "micro": {
        "min_equity": 0,
        "max_equity": 1000,
        "upgrade_above": 1100,
        "downgrade_below": 0,
        "max_positions": 1,
        "core_pct": 0.45,
        "ipo_pct": 0.15,
        "day_trade_pct": 0.10,
        "reserve_pct": 0.25,
        "max_trade_pct": 0.25,
        "max_day_trade_pct": 0.08,
        "max_ipo_trade_pct": 0.18,
        "rotation_hurdle": 25,
    },
    "small": {
        "min_equity": 1000,
        "max_equity": 3000,
        "upgrade_above": 3300,
        "downgrade_below": 900,
        "max_positions": 2,
        "core_pct": 0.50,
        "ipo_pct": 0.15,
        "day_trade_pct": 0.10,
        "reserve_pct": 0.20,
        "max_trade_pct": 0.22,
        "max_day_trade_pct": 0.07,
        "max_ipo_trade_pct": 0.16,
        "rotation_hurdle": 22,
    },
    "starter": {
        "min_equity": 3000,
        "max_equity": 10000,
        "upgrade_above": 11000,
        "downgrade_below": 2700,
        "max_positions": 4,
        "core_pct": 0.55,
        "ipo_pct": 0.12,
        "day_trade_pct": 0.08,
        "reserve_pct": 0.18,
        "max_trade_pct": 0.20,
        "max_day_trade_pct": 0.06,
        "max_ipo_trade_pct": 0.14,
        "rotation_hurdle": 18,
    },
    "growth": {
        "min_equity": 10000,
        "max_equity": 25000,
        "upgrade_above": 27500,
        "downgrade_below": 9000,
        "max_positions": 5,
        "core_pct": 0.60,
        "ipo_pct": 0.10,
        "day_trade_pct": 0.06,
        "reserve_pct": 0.15,
        "max_trade_pct": 0.18,
        "max_day_trade_pct": 0.05,
        "max_ipo_trade_pct": 0.12,
        "rotation_hurdle": 15,
    },
}

BUCKET_ORDER = ["core_capital", "ipo_capital", "day_trade_capital", "reserve_cash", "pending_cash", "profit_reserve", "tax_reserve"]


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


def safe_round(value: Any, digits: int = 2) -> Optional[float]:
    number = safe_float(value)
    if number is None:
        return None
    return round(number, digits)


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
        with path.open(newline="") as f:
            return list(csv.DictReader(f)), None
    except Exception as exc:
        return [], f"error reading {path.name}: {type(exc).__name__}: {exc}"


def first_value(row: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", "None", "nan", "NaN"):
            return value
    return default


def parse_timestamp(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    clean = raw.replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            if fmt:
                parsed = datetime.strptime(raw[:19], fmt)
                return parsed.replace(tzinfo=timezone.utc)
            parsed = datetime.fromisoformat(clean)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def stable_equity_from_history(history_rows: List[Dict[str, str]], current_equity: float) -> float:
    values: List[Tuple[datetime, float]] = []
    for row in history_rows:
        ts = parse_timestamp(row.get("timestamp"))
        equity = safe_float(first_value(row, ("equity", "portfolio_value", "account_equity")))
        if ts and equity is not None and equity > 0:
            values.append((ts, equity))
    if not values:
        return round(current_equity, 2)
    values = sorted(values, key=lambda x: x[0])[-20:]
    # Approximate 5-day average from latest 20 snapshots, safe for sparse history.
    recent = [v for _, v in values[-20:]]
    if not recent:
        return round(current_equity, 2)
    return round(sum(recent) / len(recent), 2)


def determine_tier(stable_equity: float) -> str:
    if stable_equity < 1000:
        return "micro"
    if stable_equity < 3000:
        return "small"
    if stable_equity < 10000:
        return "starter"
    return "growth"


def infer_realized_profit(capital: Dict[str, Any], history_rows: List[Dict[str, str]], trades: List[Dict[str, str]]) -> float:
    for key in ("realized_pl", "realized_profit", "closed_pl", "all_time_realized_pl"):
        value = safe_float(capital.get(key))
        if value is not None:
            return round(value, 2)

    # Fallback: sum obvious realized P/L columns from trade history.
    total = 0.0
    found = False
    for trade in trades:
        value = first_value(trade, ("realized_pl", "pnl", "pl", "profit_loss", "net_pl"))
        number = safe_float(value)
        if number is not None:
            total += number
            found = True
    if found:
        return round(total, 2)

    # Last fallback: equity over configured starting capital, conservative.
    equity = safe_float(first_value(capital, ("equity", "portfolio_value")), 0) or 0
    return round(max(0, equity - DEFAULT_STARTING_CAPITAL), 2)


def build_buckets(equity: float, cash: float, deployable_cash: float, tier: str, realized_profit: float) -> Dict[str, Dict[str, Any]]:
    rules = TIER_RULES[tier]
    tax_reserve = round(max(0, realized_profit) * DEFAULT_TAX_RATE, 2)
    profit_reserve = round(max(0, realized_profit) * 0.10, 2)  # tracked, not necessarily withdrawn.
    reserve_cash = round(max(0, equity * rules["reserve_pct"]), 2)

    # Pending cash is a safe placeholder for deposits. With no deposit ledger yet,
    # keep it zero and expose the bucket so deposits can be staged later.
    pending_cash = 0.0

    allocatable = max(0.0, min(cash, deployable_cash) - tax_reserve - pending_cash)
    core = round(max(0, equity * rules["core_pct"]), 2)
    ipo = round(max(0, equity * rules["ipo_pct"]), 2)
    day = round(max(0, equity * rules["day_trade_pct"]), 2)

    buckets = {
        "core_capital": {
            "target_dollars": core,
            "available_dollars": round(min(allocatable, core), 2),
            "deployable": True,
            "purpose": "Normal high-quality swing/core opportunities.",
        },
        "ipo_capital": {
            "target_dollars": ipo,
            "available_dollars": round(min(allocatable, ipo), 2),
            "deployable": True,
            "purpose": "High-risk IPO/catalyst/hype opportunities only.",
        },
        "day_trade_capital": {
            "target_dollars": day,
            "available_dollars": round(min(allocatable, day), 2),
            "deployable": True,
            "purpose": "High-frequency learning/day-trade opportunities; shadow-first.",
        },
        "reserve_cash": {
            "target_dollars": reserve_cash,
            "available_dollars": reserve_cash,
            "deployable": False,
            "purpose": "Capital protection buffer.",
        },
        "pending_cash": {
            "target_dollars": pending_cash,
            "available_dollars": pending_cash,
            "deployable": False,
            "purpose": "New deposits staged before becoming deployable.",
        },
        "profit_reserve": {
            "target_dollars": profit_reserve,
            "available_dollars": profit_reserve,
            "deployable": False,
            "purpose": "Tracks profits that may later be reserved/withdrawn after edge is proven.",
        },
        "tax_reserve": {
            "target_dollars": tax_reserve,
            "available_dollars": tax_reserve,
            "deployable": False,
            "purpose": "Estimated tax set-aside from realized gains; never tradable.",
        },
    }
    return buckets


def classify_setup_bucket(setup_type: str, source: str = "") -> str:
    text = f"{setup_type} {source}".lower()
    if "ipo" in text:
        return "ipo_capital"
    if "day" in text or "intraday" in text or "scalp" in text:
        return "day_trade_capital"
    return "core_capital"


def confidence_multiplier(confidence: str, sample_label: str = "") -> float:
    text = f"{confidence} {sample_label}".lower()
    if "high" in text or "meaningful" in text:
        return 1.0
    if "medium" in text or "early" in text:
        return 0.6
    return 0.25


def setup_stats_map(setup_outcomes: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(setup_outcomes, dict):
        return {}
    setups = setup_outcomes.get("setups") or setup_outcomes.get("by_setup") or setup_outcomes.get("summary") or {}
    return setups if isinstance(setups, dict) else {}


def score_opportunity(row: Dict[str, Any], setup_stats: Dict[str, Dict[str, Any]], comparison: Dict[str, Any]) -> Dict[str, Any]:
    setup = str(row.get("setup_type") or row.get("setup") or "unknown")
    score = safe_float(first_value(row, ("score", "edge_score", "rotation_score")), 0) or 0
    return_pct = safe_float(first_value(row, ("return_pct", "next_5d_return", "avg_5d", "avg_return_pct")), 0) or 0
    stats = setup_stats.get(setup, {}) if isinstance(setup_stats, dict) else {}
    avg_5d = safe_float(first_value(stats, ("avg_5d", "avg_return_pct", "avg_5d_return")), 0) or 0
    win_rate = safe_float(first_value(stats, ("win_rate",)), 0) or 0
    sample_size = int(safe_float(first_value(stats, ("count", "sample_size", "total")), 0) or 0)

    sample_bonus = 0
    if sample_size >= 300:
        sample_bonus = 15
    elif sample_size >= 100:
        sample_bonus = 8
    elif sample_size >= 25:
        sample_bonus = 2

    quality = (score * 0.45) + (return_pct * 3.0) + (avg_5d * 2.0) + (win_rate * 0.2) + sample_bonus
    return {
        "setup_type": setup,
        "quality_score": round(quality, 2),
        "raw_score": round(score, 2),
        "expected_return_pct": round(return_pct or avg_5d, 3),
        "sample_size": sample_size,
        "win_rate": round(win_rate, 2),
        "sample_label": "meaningful_signal" if sample_size >= 300 else ("early_signal" if sample_size >= 100 else "informational_only"),
        "confidence": "high" if sample_size >= 300 else ("medium" if sample_size >= 100 else "low"),
    }


def collect_opportunities(shadow_execution: Dict[str, Any], comparison: Dict[str, Any], setup_outcomes: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    setup_stats = setup_stats_map(setup_outcomes)

    for row in shadow_execution.get("top_shadow_trades", []) if isinstance(shadow_execution, dict) else []:
        if isinstance(row, dict):
            base = dict(row)
            base["opportunity_source"] = "shadow_execution"
            rows.append(base)

    for row in comparison.get("missed_winners", []) if isinstance(comparison, dict) else []:
        if isinstance(row, dict):
            base = dict(row)
            base["opportunity_source"] = "missed_winner"
            rows.append(base)

    scored: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        symbol = str(first_value(row, ("symbol", "ticker"), "UNKNOWN") or "UNKNOWN").upper()
        setup = str(first_value(row, ("setup_type", "setup"), "unknown") or "unknown")
        key = (symbol, setup, row.get("opportunity_source"))
        if key in seen:
            continue
        seen.add(key)
        metrics = score_opportunity(row, setup_stats, comparison)
        bucket = classify_setup_bucket(setup, str(row.get("opportunity_source", "")))
        scored.append({
            "symbol": symbol,
            "setup_type": setup,
            "bucket": bucket,
            "opportunity_source": row.get("opportunity_source"),
            "quality_score": metrics["quality_score"],
            "raw_score": metrics["raw_score"],
            "expected_return_pct": metrics["expected_return_pct"],
            "sample_size": metrics["sample_size"],
            "sample_label": metrics["sample_label"],
            "confidence": metrics["confidence"],
            "why": first_value(row, ("why", "reason", "decision_reason", "summary"), "Research opportunity from shadow pipeline."),
        })
    return sorted(scored, key=lambda x: x["quality_score"], reverse=True)


def recent_losing_streak(trades: List[Dict[str, str]]) -> int:
    normalized = []
    for trade in trades:
        ts = parse_timestamp(first_value(trade, ("exit_time", "closed_at", "timestamp", "time", "date", "entry_time"))) or datetime.min.replace(tzinfo=timezone.utc)
        ret = safe_float(first_value(trade, ("return_pct", "pnl_pct", "pl_pct", "profit_pct")))
        pnl = safe_float(first_value(trade, ("realized_pl", "pnl", "pl", "profit_loss", "net_pl")))
        is_loss = (ret is not None and ret < 0) or (ret is None and pnl is not None and pnl < 0)
        normalized.append((ts, is_loss))
    streak = 0
    for _, is_loss in sorted(normalized, key=lambda x: x[0], reverse=True):
        if is_loss:
            streak += 1
        else:
            break
    return streak


def detect_risk_clusters(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_bucket = Counter(o.get("bucket", "unknown") for o in opportunities[:10])
    by_setup = Counter(o.get("setup_type", "unknown") for o in opportunities[:10])
    clusters = []
    for name, count in by_bucket.items():
        if count >= 3:
            clusters.append({"cluster_type": "bucket", "name": name, "count": count, "warning": "Multiple top opportunities share the same risk bucket."})
    for name, count in by_setup.items():
        if count >= 3:
            clusters.append({"cluster_type": "setup_type", "name": name, "count": count, "warning": "Multiple top opportunities share the same setup type."})
    return clusters


def allocate_shadow(opportunities: List[Dict[str, Any]], buckets: Dict[str, Dict[str, Any]], equity: float, tier: str, losing_streak: int) -> List[Dict[str, Any]]:
    rules = TIER_RULES[tier]
    remaining = {name: safe_float(data.get("available_dollars"), 0) or 0 for name, data in buckets.items()}
    max_positions = int(rules["max_positions"])
    decisions: List[Dict[str, Any]] = []
    funded = 0

    for opp in opportunities[:25]:
        bucket = opp.get("bucket", "core_capital")
        bucket_available = remaining.get(bucket, 0)
        confidence = opp.get("confidence", "low")
        quality = safe_float(opp.get("quality_score"), 0) or 0
        mult = confidence_multiplier(confidence, opp.get("sample_label", ""))

        if bucket == "day_trade_capital":
            max_pct = rules["max_day_trade_pct"]
        elif bucket == "ipo_capital":
            max_pct = rules["max_ipo_trade_pct"]
        else:
            max_pct = rules["max_trade_pct"]

        if losing_streak >= 3:
            max_pct *= 0.5
            mult *= 0.5

        suggested = round(max(0, equity * max_pct * mult), 2)
        suggested = min(suggested, bucket_available)

        reasons = []
        if funded >= max_positions:
            decision = "watch_only_max_positions_reached"
            suggested = 0
            reasons.append("Tier max position count reached.")
        elif bucket_available <= 0:
            decision = "watch_only_no_bucket_cash"
            suggested = 0
            reasons.append(f"No deployable cash in {bucket}.")
        elif confidence == "low":
            decision = "shadow_watch_low_confidence"
            suggested = round(min(suggested, equity * 0.05), 2)
            reasons.append("Low confidence: informational only sizing.")
        elif quality < 50:
            decision = "skip_low_quality"
            suggested = 0
            reasons.append("Quality score below allocator threshold.")
        else:
            decision = "shadow_allocate"
            reasons.append("Opportunity passed shadow allocation screen.")

        if bucket == "day_trade_capital":
            reasons.append("Day trading remains shadow-first and PDT-aware for small accounts.")
        if bucket == "ipo_capital":
            reasons.append("IPO/catalyst setup uses separate high-risk bucket; do not pull from core automatically.")
        if losing_streak >= 3:
            reasons.append("Recent losing streak detected: allocation reduced.")

        if suggested > 0 and decision in {"shadow_allocate", "shadow_watch_low_confidence"}:
            remaining[bucket] = round(max(0, remaining[bucket] - suggested), 2)
            funded += 1

        decisions.append({
            "symbol": opp.get("symbol"),
            "setup_type": opp.get("setup_type"),
            "bucket": bucket,
            "decision": decision,
            "suggested_allocation_pct": round((suggested / equity) * 100, 2) if equity else 0,
            "suggested_dollar_amount": round(suggested, 2),
            "quality_score": opp.get("quality_score"),
            "expected_return_pct": opp.get("expected_return_pct"),
            "confidence": confidence,
            "sample_size": opp.get("sample_size"),
            "sample_label": opp.get("sample_label"),
            "was_capital_available": bucket_available > 0,
            "would_this_have_been_taken": suggested > 0 and decision in {"shadow_allocate", "shadow_watch_low_confidence"},
            "why": " ".join(reasons) or opp.get("why"),
            "source": opp.get("opportunity_source"),
            "automation_allowed": False,
        })
    return decisions


def edge_validation(comparison: Dict[str, Any], setup_outcomes: Dict[str, Any]) -> Dict[str, Any]:
    summary = comparison.get("summary", {}) if isinstance(comparison, dict) else {}
    sample = int(safe_float(first_value(summary, ("evaluated_shadow_opportunities_count", "shadow_opportunities_count")), 0) or 0)
    confidence = str(first_value(summary, ("confidence",), "low") or "low").lower()
    avg_shadow = safe_float(summary.get("average_shadow_return_pct"), 0) or 0
    bad_rate = safe_float(summary.get("bad_live_trade_rate"), 100) or 100
    edge_proven = sample >= 300 and confidence == "high" and avg_shadow > 0 and bad_rate < 35
    return {
        "edge_proven": edge_proven,
        "withdrawal_enabled": False if not edge_proven else True,
        "reason": "Withdrawals stay disabled until sample size, confidence, returns, and drawdown/risk are proven." if not edge_proven else "Edge gate passed; withdrawals may be reviewed manually.",
        "requirements": {
            "sample_size_min": 300,
            "confidence_required": "high",
            "average_shadow_return_positive": True,
            "bad_live_trade_rate_below_pct": 35,
        },
        "current": {
            "sample_size": sample,
            "confidence": confidence,
            "average_shadow_return_pct": safe_round(avg_shadow, 3),
            "bad_live_trade_rate": safe_round(bad_rate, 2),
        },
    }


def build_rotation_decisions(rotation: Dict[str, Any], buckets: Dict[str, Dict[str, Any]], equity: float, tier: str) -> List[Dict[str, Any]]:
    rules = TIER_RULES[tier]
    suggestions = rotation.get("rotation_suggestions", []) if isinstance(rotation, dict) else []
    decisions = []
    for r in suggestions[:20]:
        if not isinstance(r, dict):
            continue
        score = safe_float(r.get("rotation_score"), 0) or 0
        expected_edge = safe_float(r.get("expected_edge"), 0) or 0
        confidence = str(r.get("confidence", "low")).lower()
        hurdle = rules["rotation_hurdle"]
        if confidence == "high" and (score >= 70 or expected_edge >= hurdle):
            decision = "shadow_only_partial_rotate"
            pct = min(0.35, rules["max_trade_pct"])
            why = "Rotation edge appears meaningful, but automation remains disabled. Prefer partial rotation for small-account safety."
        elif confidence in {"medium", "high"} and (score >= 60 or expected_edge >= hurdle * 0.7):
            decision = "watch_rotation"
            pct = 0.0
            why = "Potential rotation, but edge or confidence is not strong enough for capital movement."
        else:
            decision = "hold_current_position"
            pct = 0.0
            why = "Rotation hurdle not met. Avoid churn."
        decisions.append({
            "sell_symbol": r.get("sell_symbol"),
            "buy_symbol": r.get("buy_symbol"),
            "rotation_score": safe_round(score, 2),
            "expected_edge": safe_round(expected_edge, 2),
            "confidence": confidence,
            "rotation_decision": decision,
            "capital_to_move_pct": round(pct * 100, 2),
            "capital_to_move_dollars": round(equity * pct, 2),
            "why": why,
            "automation_allowed": False,
        })
    return decisions


def main() -> Dict[str, Any]:
    warnings: List[str] = []
    capital, warning = read_json(CAPITAL, {})
    if warning:
        warnings.append(warning)
    comparison, warning = read_json(SHADOW_LIVE, {})
    if warning:
        warnings.append(warning)
    shadow_execution, warning = read_json(SHADOW_EXECUTION, {})
    if warning:
        warnings.append(warning)
    setup_outcomes, warning = read_json(SETUP_OUTCOMES, {})
    if warning:
        warnings.append(warning)
    rotation, warning = read_json(ROTATION, {})
    if warning:
        warnings.append(warning)
    bot_status, warning = read_json(BOT_STATUS, {})
    if warning:
        warnings.append(warning)
    history_rows, warning = read_csv(CAPITAL_HISTORY)
    if warning:
        warnings.append(warning)
    trades, warning = read_csv(TRADE_HISTORY)
    if warning:
        warnings.append(warning)

    equity = safe_float(first_value(capital, ("equity", "portfolio_value", "account_equity")), DEFAULT_STARTING_CAPITAL) or DEFAULT_STARTING_CAPITAL
    cash = safe_float(first_value(capital, ("cash", "buying_power")), equity) or equity
    deployable_cash = safe_float(capital.get("deployable_cash"), max(0, cash * 0.7)) or 0
    stable_equity = stable_equity_from_history(history_rows, equity)
    tier = determine_tier(stable_equity)
    tier_rules = TIER_RULES[tier]
    realized_profit = infer_realized_profit(capital, history_rows, trades)
    buckets = build_buckets(equity, cash, deployable_cash, tier, realized_profit)
    opportunities = collect_opportunities(shadow_execution, comparison, setup_outcomes)
    streak = recent_losing_streak(trades)
    allocation_decisions = allocate_shadow(opportunities, buckets, equity, tier, streak)
    clusters = detect_risk_clusters(opportunities)
    edge_gate = edge_validation(comparison, setup_outcomes)
    rotation_decisions = build_rotation_decisions(rotation, buckets, equity, tier)

    suggested_total = sum(safe_float(d.get("suggested_dollar_amount"), 0) or 0 for d in allocation_decisions)
    top_decision = next((d for d in allocation_decisions if d.get("would_this_have_been_taken")), allocation_decisions[0] if allocation_decisions else {})

    output = {
        "generated_at": utc_now(),
        "updated_at": utc_now(),
        "version": "shadow_capital_allocator_v2",
        "status": "research_only",
        "mode": "shadow_allocation_only",
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "live_trading_changed": False,
            "automation_allowed": False,
            "note": "This file is dashboard/research output only. It does not place trades or alter live logic.",
        },
        "policy": {
            "profit_policy": PROFIT_POLICY,
            "withdrawal_policy": "disabled_until_edge_proven_then_manual_review",
            "tax_reserve_enabled": True,
            "estimated_tax_rate": DEFAULT_TAX_RATE,
            "deposits_policy": "new_cash_goes_to_pending_bucket_before_gradual_deployment",
            "tier_policy": "stable_equity_with_buffers_not_instant_balance",
            "rotation_policy": "allocator_is_gatekeeper; shadow-only until proven",
        },
        "account": {
            "equity": safe_round(equity, 2),
            "cash": safe_round(cash, 2),
            "deployable_cash_reported": safe_round(deployable_cash, 2),
            "stable_equity": safe_round(stable_equity, 2),
            "tier": tier,
            "tier_rules": tier_rules,
            "realized_profit_estimate": safe_round(realized_profit, 2),
            "recent_losing_streak": streak,
        },
        "capital_buckets": buckets,
        "summary": {
            "opportunities_seen": len(opportunities),
            "allocation_decisions": len(allocation_decisions),
            "shadow_allocations": sum(1 for d in allocation_decisions if d.get("would_this_have_been_taken")),
            "suggested_total_dollars": round(suggested_total, 2),
            "suggested_total_pct": round((suggested_total / equity) * 100, 2) if equity else 0,
            "top_decision": top_decision,
            "risk_clusters": len(clusters),
            "edge_proven": edge_gate.get("edge_proven"),
            "withdrawal_enabled": edge_gate.get("withdrawal_enabled"),
        },
        "allocation_decisions": allocation_decisions,
        "rotation_decisions": rotation_decisions,
        "risk_controls": {
            "risk_clusters": clusters,
            "losing_streak_protection_active": streak >= 3,
            "small_account_churn_control": {
                "max_positions": tier_rules["max_positions"],
                "rotation_hurdle": tier_rules["rotation_hurdle"],
                "max_one_rotation_per_day_recommended": tier in {"micro", "small", "starter"},
            },
            "pdt_day_trade_warning": "Day-trade bucket is shadow-first and should remain PDT-aware for accounts under $25k.",
        },
        "edge_validation_gate": edge_gate,
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
                "Do not withdraw if it breaks tier buffers or reduces active-trade protection.",
            ],
        },
        "data_quality": {
            "warnings": warnings,
            "missing_sources": [w for w in warnings if str(w).startswith("missing:")],
            "inputs_present": {
                "capital_intelligence": bool(capital),
                "shadow_live_comparison": bool(comparison),
                "shadow_execution": bool(shadow_execution),
                "setup_outcomes": bool(setup_outcomes),
                "rotation_engine": bool(rotation),
                "trade_history_rows": len(trades),
                "capital_history_rows": len(history_rows),
            },
        },
        "explanation": [
            "Allocator v2 is a shadow-only capital router, not a trading engine.",
            "It separates core, IPO, day-trade, reserve, pending, profit, and tax buckets.",
            "It prioritizes reinvestment until edge is proven and withdrawals pass manual review.",
            "Rotation decisions are evaluated but never automated here.",
        ],
    }

    RESEARCH_OUT.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(json.dumps(output, indent=2, sort_keys=True))
    return output


if __name__ == "__main__":
    main()
