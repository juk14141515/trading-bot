"""
Research-only shadow evaluation engine for Ponder Invest AI.

This file evaluates shadow/research recommendations only. It does not place
orders, modify Alpaca execution, rotate positions, or change live bot logic.

Manual run:
    python3 shadow_evaluator.py
    python3 -m shadow_evaluator

Outputs:
    static/research/rotation_performance_latest.json
    static/research/shadow_learning_latest.json
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yfinance as yf
except Exception:  # pragma: no cover - runtime dependency on VPS
    yf = None

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "static" / "research"
PERFORMANCE_FILE = RESEARCH_DIR / "rotation_performance_latest.json"
LEARNING_FILE = RESEARCH_DIR / "shadow_learning_latest.json"
ROTATION_FILE = RESEARCH_DIR / "rotation_engine_latest.json"
SELL_FILE = RESEARCH_DIR / "sell_intelligence_latest.json"
SHADOW_ALLOCATOR_FILE = RESEARCH_DIR / "shadow_capital_allocator_latest.json"

OUTCOME_HELPED_THRESHOLD = 0.005
OUTCOME_HURT_THRESHOLD = -0.005
DEFAULT_WINDOWS = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
}
HORIZON_ALIASES = {
    "60m": "1h",
    "1hr": "1h",
    "24h": "1d",
    "1day": "1d",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat(timespec="seconds")


def parse_time(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), timezone.utc)
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    for suffix in ("Z", "+00:00"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    formats = (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


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


def clean_text(value: Any, default: str = "") -> str:
    if value in (None, "", "undefined"):
        return default
    return str(value)


def normalize_horizon(value: Any) -> str:
    raw = clean_text(value, "1h").lower().replace(" ", "")
    return HORIZON_ALIASES.get(raw, raw)


def horizon_delta(horizon: str) -> timedelta:
    horizon = normalize_horizon(horizon)
    if horizon in DEFAULT_WINDOWS:
        return DEFAULT_WINDOWS[horizon]
    if horizon.endswith("m"):
        return timedelta(minutes=int(clean_number(horizon[:-1], 60) or 60))
    if horizon.endswith("h"):
        return timedelta(hours=int(clean_number(horizon[:-1], 1) or 1))
    if horizon.endswith("d"):
        return timedelta(days=int(clean_number(horizon[:-1], 1) or 1))
    return timedelta(hours=1)


def make_id(row: Dict[str, Any]) -> str:
    existing = clean_text(row.get("id"), "")
    if existing:
        return existing
    pieces = [
        clean_text(row.get("signal_timestamp") or row.get("timestamp") or row.get("created_at"), ""),
        clean_text(row.get("type") or row.get("idea_type") or "rotation", "rotation"),
        clean_text(row.get("sell_symbol") or row.get("from_symbol"), ""),
        clean_text(row.get("buy_symbol") or row.get("to_symbol"), ""),
        normalize_horizon(row.get("horizon")),
        clean_text(row.get("action") or row.get("recommendation"), ""),
    ]
    return hashlib.sha1("|".join(pieces).encode("utf-8")).hexdigest()[:16]


def get_symbol(row: Dict[str, Any], *names: str) -> str:
    for name in names:
        value = clean_text(row.get(name), "")
        if value and value.upper() not in {"NONE", "N/A", "UNKNOWN"}:
            return value.upper()
    return ""


def normalize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    record = dict(row)
    record["id"] = make_id(record)
    record["type"] = clean_text(record.get("type") or record.get("idea_type"), "rotation").lower()
    record["horizon"] = normalize_horizon(record.get("horizon"))
    record["signal_timestamp"] = clean_text(
        record.get("signal_timestamp") or record.get("timestamp") or record.get("created_at"),
        iso_now(),
    )
    record["from_symbol"] = get_symbol(record, "from_symbol", "sell_symbol", "symbol")
    record["to_symbol"] = get_symbol(record, "to_symbol", "buy_symbol")
    record["sell_symbol"] = record.get("sell_symbol") or record["from_symbol"]
    record["buy_symbol"] = record.get("buy_symbol") or record["to_symbol"]
    record["action"] = clean_text(record.get("action") or record.get("recommendation"), "Research idea")
    record["confidence"] = record.get("confidence") if record.get("confidence") not in ("undefined", "") else None
    record["reason"] = clean_text(record.get("reason"), "Not evaluated yet")

    status = clean_text(record.get("status"), "pending").lower()
    outcome = clean_text(record.get("outcome") or record.get("result"), "")
    alpha = clean_number(record.get("alpha"), None)
    alpha_pct = clean_number(record.get("alpha_pct") or record.get("avg_alpha_pct"), None)
    if alpha is None and alpha_pct is not None:
        alpha = alpha_pct / 100.0
    if alpha_pct is None and alpha is not None:
        alpha_pct = alpha * 100.0

    if outcome in {"helped", "hurt", "neutral"}:
        status = "evaluated"
    elif status not in {"evaluated", "pending", "unresolved", "skipped"}:
        status = "pending"

    record["status"] = status
    record["outcome"] = outcome if outcome in {"helped", "hurt", "neutral"} else None
    record["result"] = record["outcome"] or "Pending"
    record["alpha"] = alpha
    record["alpha_pct"] = round(alpha_pct, 4) if alpha_pct is not None else None
    return record


def price_at_or_after(symbol: str, when: datetime, max_lookahead: timedelta = timedelta(minutes=20)) -> Optional[float]:
    if not symbol or yf is None:
        return None
    start = when - timedelta(minutes=5)
    end = when + max_lookahead
    now = utc_now()
    if start > now:
        return None
    if end > now:
        end = now
    if end <= start:
        return None

    # 5m bars are available longer than 1m bars and are enough for research labels.
    try:
        data = yf.download(
            symbol,
            start=start.strftime("%Y-%m-%d"),
            end=(end + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="5m",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception:
        return None
    if data is None or data.empty or "Close" not in data:
        return None

    try:
        frame = data.copy()
        if getattr(frame.index, "tz", None) is None:
            frame.index = frame.index.tz_localize(timezone.utc)
        else:
            frame.index = frame.index.tz_convert(timezone.utc)
        window = frame[(frame.index >= start) & (frame.index <= end)]
        if window.empty:
            return None
        close = window["Close"].dropna()
        if close.empty:
            return None
        value = close.iloc[0]
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        return clean_number(value, None)
    except Exception:
        return None


def latest_price(symbol: str) -> Optional[float]:
    if not symbol or yf is None:
        return None
    try:
        data = yf.download(symbol, period="5d", interval="5m", auto_adjust=True, progress=False, threads=False)
    except Exception:
        return None
    if data is None or data.empty or "Close" not in data:
        return None
    try:
        close = data["Close"].dropna()
        if close.empty:
            return None
        value = close.iloc[-1]
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        return clean_number(value, None)
    except Exception:
        return None


def classify_alpha(alpha: float) -> str:
    if alpha > OUTCOME_HELPED_THRESHOLD:
        return "helped"
    if alpha < OUTCOME_HURT_THRESHOLD:
        return "hurt"
    return "neutral"


def evaluate_rotation(record: Dict[str, Any], now: datetime) -> Tuple[Dict[str, Any], str]:
    created = parse_time(record.get("signal_timestamp"))
    if not created:
        record["status"] = "unresolved"
        record["result"] = "Not evaluated yet"
        record["reason"] = "missing signal timestamp"
        return record, "error"

    due_at = created + horizon_delta(record.get("horizon"))
    if now < due_at:
        record["status"] = "pending"
        record["result"] = "Pending"
        record["reason"] = f"too new; due at {due_at.isoformat(timespec='seconds')}"
        return record, "too_new"

    from_symbol = record.get("from_symbol") or record.get("sell_symbol")
    to_symbol = record.get("to_symbol") or record.get("buy_symbol")
    if not from_symbol or not to_symbol:
        record["status"] = "unresolved"
        record["result"] = "Not evaluated yet"
        record["reason"] = "missing from/to symbol"
        return record, "error"

    entry_from = clean_number(record.get("entry_from_price") or record.get("from_entry_price") or record.get("sell_entry_price"), None)
    entry_to = clean_number(record.get("entry_to_price") or record.get("to_entry_price") or record.get("buy_entry_price"), None)
    if entry_from is None:
        entry_from = price_at_or_after(from_symbol, created)
    if entry_to is None:
        entry_to = price_at_or_after(to_symbol, created)

    exit_from = clean_number(record.get("exit_from_price") or record.get("from_exit_price") or record.get("sell_exit_price"), None)
    exit_to = clean_number(record.get("exit_to_price") or record.get("to_exit_price") or record.get("buy_exit_price"), None)
    if exit_from is None:
        exit_from = price_at_or_after(from_symbol, due_at) or latest_price(from_symbol)
    if exit_to is None:
        exit_to = price_at_or_after(to_symbol, due_at) or latest_price(to_symbol)

    if not entry_from or not entry_to or not exit_from or not exit_to:
        record["status"] = "pending"
        record["result"] = "Pending"
        record["reason"] = "price data unavailable"
        return record, "error"

    from_return = (exit_from - entry_from) / entry_from
    to_return = (exit_to - entry_to) / entry_to
    alpha = to_return - from_return
    outcome = classify_alpha(alpha)

    record.update(
        {
            "status": "evaluated",
            "result": outcome,
            "outcome": outcome,
            "alpha": round(alpha, 6),
            "alpha_pct": round(alpha * 100, 4),
            "from_return": round(from_return, 6),
            "to_return": round(to_return, 6),
            "from_return_pct": round(from_return * 100, 4),
            "to_return_pct": round(to_return * 100, 4),
            "entry_from_price": round(entry_from, 4),
            "entry_to_price": round(entry_to, 4),
            "exit_from_price": round(exit_from, 4),
            "exit_to_price": round(exit_to, 4),
            "evaluated_at": iso_now(),
            "due_at": due_at.isoformat(timespec="seconds"),
            "reason": f"{record.get('horizon')} alpha = to_return - from_return",
        }
    )
    return record, "evaluated"


def evaluate_sell(record: Dict[str, Any], now: datetime) -> Tuple[Dict[str, Any], str]:
    created = parse_time(record.get("signal_timestamp"))
    if not created:
        record["status"] = "unresolved"
        record["result"] = "Not evaluated yet"
        record["reason"] = "missing signal timestamp"
        return record, "error"
    due_at = created + horizon_delta(record.get("horizon"))
    if now < due_at:
        record["status"] = "pending"
        record["result"] = "Pending"
        record["reason"] = f"too new; due at {due_at.isoformat(timespec='seconds')}"
        return record, "too_new"

    symbol = record.get("from_symbol") or record.get("sell_symbol") or record.get("symbol")
    entry = clean_number(record.get("entry_price") or record.get("entry_from_price"), None) or price_at_or_after(symbol, created)
    exit_price = clean_number(record.get("exit_price") or record.get("exit_from_price"), None) or price_at_or_after(symbol, due_at) or latest_price(symbol)
    if not symbol or not entry or not exit_price:
        record["status"] = "pending"
        record["result"] = "Pending"
        record["reason"] = "price data unavailable"
        return record, "error"

    move = (exit_price - entry) / entry
    # For sell/trim warnings, downside after the warning means the warning helped.
    if move < OUTCOME_HURT_THRESHOLD:
        outcome = "helped"
    elif move > OUTCOME_HELPED_THRESHOLD:
        outcome = "hurt"
    else:
        outcome = "neutral"

    record.update(
        {
            "status": "evaluated",
            "result": outcome,
            "outcome": outcome,
            "alpha": round(-move, 6),
            "alpha_pct": round(-move * 100, 4),
            "symbol_return": round(move, 6),
            "symbol_return_pct": round(move * 100, 4),
            "entry_price": round(entry, 4),
            "exit_price": round(exit_price, 4),
            "evaluated_at": iso_now(),
            "due_at": due_at.isoformat(timespec="seconds"),
            "reason": f"{record.get('horizon')} sell-warning outcome from price move",
        }
    )
    return record, "evaluated"


def safe_percent(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round((numerator / denominator) * 100, 2)


def summarize(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(records)
    evaluated = [r for r in rows if r.get("status") == "evaluated" and r.get("outcome") in {"helped", "hurt", "neutral"}]
    pending = [r for r in rows if r.get("status") != "evaluated"]
    helped = [r for r in evaluated if r.get("outcome") == "helped"]
    hurt = [r for r in evaluated if r.get("outcome") == "hurt"]
    neutral = [r for r in evaluated if r.get("outcome") == "neutral"]
    alphas = [clean_number(r.get("alpha"), None) for r in evaluated]
    alphas = [a for a in alphas if a is not None]
    by_type: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"evaluated": 0, "pending": 0, "helped": 0, "hurt": 0, "neutral": 0})
    by_horizon: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"evaluated": 0, "pending": 0, "helped": 0, "hurt": 0, "neutral": 0, "win_rate": None, "avg_alpha_pct": None})

    for r in rows:
        typ = clean_text(r.get("type"), "unknown")
        horizon = normalize_horizon(r.get("horizon"))
        if r.get("status") == "evaluated" and r.get("outcome") in {"helped", "hurt", "neutral"}:
            by_type[typ]["evaluated"] += 1
            by_type[typ][r.get("outcome")] += 1
            by_horizon[horizon]["evaluated"] += 1
            by_horizon[horizon][r.get("outcome")] += 1
        else:
            by_type[typ]["pending"] += 1
            by_horizon[horizon]["pending"] += 1

    for bucket in list(by_type.values()) + list(by_horizon.values()):
        bucket["win_rate"] = safe_percent(bucket.get("helped", 0), bucket.get("evaluated", 0))

    for horizon, bucket in by_horizon.items():
        horizon_alphas = [clean_number(r.get("alpha"), None) for r in evaluated if normalize_horizon(r.get("horizon")) == horizon]
        horizon_alphas = [a for a in horizon_alphas if a is not None]
        bucket["avg_alpha_pct"] = round((sum(horizon_alphas) / len(horizon_alphas)) * 100, 4) if horizon_alphas else None

    best = max(evaluated, key=lambda r: clean_number(r.get("alpha"), -999), default=None)
    worst = min(evaluated, key=lambda r: clean_number(r.get("alpha"), 999), default=None)

    return {
        "total_records": len(rows),
        "evaluated": len(evaluated),
        "pending": len(pending),
        "pending_evaluations": len(pending),
        "helped": len(helped),
        "hurt": len(hurt),
        "neutral": len(neutral),
        "win_rate": safe_percent(len(helped), len(evaluated)),
        "win_rate_label": f"{safe_percent(len(helped), len(evaluated))}%" if evaluated else "No evaluated decisions yet",
        "avg_alpha": round(sum(alphas) / len(alphas), 6) if alphas else None,
        "avg_alpha_pct": round((sum(alphas) / len(alphas)) * 100, 4) if alphas else None,
        "best_idea": best,
        "worst_idea": worst,
        "by_type": dict(by_type),
        "by_horizon": dict(by_horizon),
    }


def dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for raw in records:
        record = normalize_record(raw)
        existing = merged.get(record["id"])
        if existing is None:
            merged[record["id"]] = record
            continue
        # Prefer evaluated records over pending records, otherwise keep latest normalized fields.
        if existing.get("status") != "evaluated" and record.get("status") == "evaluated":
            merged[record["id"]] = record
        else:
            existing.update({k: v for k, v in record.items() if v not in (None, "", "undefined")})
    return list(merged.values())


def load_existing_records() -> List[Dict[str, Any]]:
    performance = read_json(PERFORMANCE_FILE, {})
    records = performance.get("evaluations") or performance.get("records") or []
    return [r for r in records if isinstance(r, dict)]


def create_current_research_records() -> List[Dict[str, Any]]:
    """Create pending records from latest research feeds when they expose ideas.

    Existing performance evaluations remain the primary source. These additions are
    intentionally conservative and only help future runs capture current ideas with
    a consistent schema.
    """
    created_at = iso_now()
    records: List[Dict[str, Any]] = []

    rotation = read_json(ROTATION_FILE, {})
    for idea in rotation.get("rotation_suggestions", []) or []:
        if not isinstance(idea, dict):
            continue
        for horizon in DEFAULT_WINDOWS:
            records.append(
                {
                    "type": "rotation",
                    "signal_timestamp": idea.get("timestamp") or rotation.get("updated_at") or created_at,
                    "horizon": horizon,
                    "from_symbol": idea.get("from_symbol") or idea.get("sell_symbol"),
                    "to_symbol": idea.get("to_symbol") or idea.get("buy_symbol"),
                    "action": idea.get("action") or idea.get("recommendation") or "Rotation research idea",
                    "confidence": idea.get("confidence"),
                    "rotation_score": idea.get("rotation_score"),
                    "expected_edge": idea.get("expected_edge"),
                    "status": "pending",
                    "result": "Pending",
                    "reason": idea.get("reason") or "Not evaluated yet",
                }
            )

    shadow = read_json(SHADOW_ALLOCATOR_FILE, {})
    for idea in shadow.get("shadow_actions", []) or []:
        if not isinstance(idea, dict):
            continue
        if not (idea.get("sell_symbol") and idea.get("buy_symbol")):
            continue
        for horizon in DEFAULT_WINDOWS:
            records.append(
                {
                    "type": "rotation",
                    "signal_timestamp": idea.get("timestamp") or shadow.get("updated_at") or created_at,
                    "horizon": horizon,
                    "from_symbol": idea.get("sell_symbol"),
                    "to_symbol": idea.get("buy_symbol"),
                    "action": idea.get("recommendation") or "Shadow allocator idea",
                    "confidence": idea.get("confidence"),
                    "status": "pending",
                    "result": "Pending",
                    "reason": idea.get("reason") or "Not evaluated yet",
                }
            )

    sell = read_json(SELL_FILE, {})
    for idea in sell.get("sell_candidates", []) or []:
        if not isinstance(idea, dict):
            continue
        symbol = idea.get("symbol")
        if not symbol:
            continue
        for horizon in DEFAULT_WINDOWS:
            records.append(
                {
                    "type": "sell",
                    "signal_timestamp": idea.get("timestamp") or sell.get("updated_at") or created_at,
                    "horizon": horizon,
                    "from_symbol": symbol,
                    "sell_symbol": symbol,
                    "action": idea.get("verdict") or idea.get("recommendation") or "Sell intelligence idea",
                    "confidence": idea.get("confidence"),
                    "sell_pressure": idea.get("sell_pressure"),
                    "status": "pending",
                    "result": "Pending",
                    "reason": ", ".join(idea.get("reasons", [])) if isinstance(idea.get("reasons"), list) else clean_text(idea.get("reason"), "Not evaluated yet"),
                }
            )
    return records


def run_evaluator(include_current_feeds: bool = True) -> Dict[str, Any]:
    now = utc_now()
    loaded = load_existing_records()
    if include_current_feeds:
        loaded.extend(create_current_research_records())
    records = dedupe(loaded)

    counts = {"pending_loaded": 0, "evaluated_now": 0, "skipped_too_new": 0, "errors": 0, "already_evaluated": 0}
    updated_records: List[Dict[str, Any]] = []

    for record in records:
        if record.get("status") == "evaluated" and record.get("outcome") in {"helped", "hurt", "neutral"}:
            counts["already_evaluated"] += 1
            updated_records.append(normalize_record(record))
            continue

        counts["pending_loaded"] += 1
        idea_type = clean_text(record.get("type"), "rotation").lower()
        if idea_type in {"sell", "trim", "exit"}:
            evaluated, state = evaluate_sell(record, now)
        else:
            evaluated, state = evaluate_rotation(record, now)

        if state == "evaluated":
            counts["evaluated_now"] += 1
        elif state == "too_new":
            counts["skipped_too_new"] += 1
        elif state == "error":
            counts["errors"] += 1
        updated_records.append(normalize_record(evaluated))

    summary = summarize(updated_records)
    output = {
        "updated_at": iso_now(),
        "version": "v3_research_only_shadow_evaluator",
        "status": "research_only",
        "summary": summary,
        "by_horizon": summary.get("by_horizon", {}),
        "by_type": summary.get("by_type", {}),
        "evaluations": updated_records,
        "run": counts,
        "notes": [
            "Research-only evaluator. Does not place orders or modify live trading logic.",
            "Rotation alpha = return(to_symbol) - return(from_symbol).",
            "Sell warning alpha is positive when price moved down after the warning.",
        ],
    }
    write_json(PERFORMANCE_FILE, output)
    write_json(LEARNING_FILE, output)
    return output


def main() -> None:
    output = run_evaluator(include_current_feeds=True)
    run = output.get("run", {})
    summary = output.get("summary", {})
    print("Ponder Shadow Evaluator complete")
    print(f"pending loaded: {run.get('pending_loaded', 0)}")
    print(f"evaluated now: {run.get('evaluated_now', 0)}")
    print(f"skipped too new: {run.get('skipped_too_new', 0)}")
    print(f"already evaluated: {run.get('already_evaluated', 0)}")
    print(f"errors/unresolved: {run.get('errors', 0)}")
    print(f"total evaluated: {summary.get('evaluated', 0)}")
    print(f"pending remaining: {summary.get('pending_evaluations', 0)}")
    print(f"win rate: {summary.get('win_rate_label')}")
    print(f"updated: {PERFORMANCE_FILE}")


if __name__ == "__main__":
    main()
