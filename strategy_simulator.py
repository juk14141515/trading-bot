"""Read-only strategy simulator for Ponder Invest AI.

This module does not place orders and does not import bot.py. It reads the
bot's existing logs / research artifacts and writes dashboard-friendly JSON
snapshots for paper, small-cap shadow, and day-trade shadow analysis.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "static" / "research"

LEARNING_LOG = ROOT / "learning_shadow_log.csv"
TRADE_HISTORY = ROOT / "trade_history.csv"
SCANNER_RESULTS = ROOT / "market_scanner_results_v2.csv"
TOP_CANDIDATES = ROOT / "top_10_candidates_v2.json"

FORWARD_SIM_OUT = RESEARCH_DIR / "forward_setup_simulations_latest.json"
BACKTEST_OUT = RESEARCH_DIR / "current_strategy_backtest_latest.json"
SETUP_PERFORMANCE_OUT = RESEARCH_DIR / "setup_performance_latest.json"

PAPER_THRESHOLD = 68
SMALL_CAP_THRESHOLD = 68
DAY_TRADE_THRESHOLD = 80
SMALL_CAP_STARTING_CASH = 500.0
SMALL_CAP_MAX_POSITION = 100.0
SMALL_CAP_MAX_POSITIONS = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
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


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def normalize_event(row: Dict[str, str]) -> Dict[str, Any]:
    return {
        "timestamp": row.get("timestamp", ""),
        "event": row.get("event", ""),
        "symbol": row.get("symbol", "-") or "-",
        "score": safe_float(row.get("score")),
        "reason": row.get("reason", ""),
        "open_pl": safe_float(row.get("open_pl")),
        "rotation_score": safe_float(row.get("rotation_score")),
        "rotation_decision": row.get("rotation_decision", ""),
        "notes": row.get("notes", ""),
    }


def learning_events() -> List[Dict[str, Any]]:
    return [normalize_event(row) for row in read_csv(LEARNING_LOG)]


def trade_rows() -> List[Dict[str, str]]:
    return read_csv(TRADE_HISTORY)


def scanner_rows() -> List[Dict[str, str]]:
    return read_csv(SCANNER_RESULTS)


def latest_top_candidates() -> List[Dict[str, Any]]:
    raw = read_json(TOP_CANDIDATES, [])
    if isinstance(raw, dict):
        for key in ("candidates", "top_candidates", "scanner_top", "items"):
            if isinstance(raw.get(key), list):
                return raw[key]
        return []
    if isinstance(raw, list):
        return raw
    return []


def summarize_trade_history(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    buys = [r for r in rows if str(r.get("side", r.get("action", ""))).lower() == "buy"]
    sells = [r for r in rows if str(r.get("side", r.get("action", ""))).lower() == "sell"]
    closed_pnls = [safe_float(r.get("pnl")) for r in sells if r.get("pnl") not in (None, "")]
    wins = [p for p in closed_pnls if p > 0]
    losses = [p for p in closed_pnls if p < 0]
    return {
        "total_rows": len(rows),
        "buys": len(buys),
        "sells": len(sells),
        "closed_with_pnl": len(closed_pnls),
        "win_rate": round((len(wins) / len(closed_pnls)) * 100, 2) if closed_pnls else 0,
        "total_pnl": round(sum(closed_pnls), 2),
        "avg_win": round(sum(wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
    }


def setup_from_reason(reason: str, notes: str = "") -> str:
    text = f"{reason} | {notes}"
    if "setup=" in text:
        try:
            return text.split("setup=", 1)[1].split("|", 1)[0].strip() or "unknown"
        except Exception:
            return "unknown"
    if "day" in text.lower():
        return "day_trade_shadow"
    if "small" in text.lower():
        return "small_cap_shadow"
    return "current_bot"


def summarize_learning(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = Counter(e["event"] for e in events)
    symbols = Counter(e["symbol"] for e in events if e["symbol"] and e["symbol"] != "-")
    latest = events[-25:]
    paper_decisions = [e for e in events if e["event"] == "LEARNING_SHADOW_BUY_DECISION" and e["score"] >= PAPER_THRESHOLD]
    small_cap = [
        e for e in events
        if e["event"] == "SHADOW_SMALL_CAP_BUY_DECISION"
        or (e["score"] >= SMALL_CAP_THRESHOLD and "small" in e.get("notes", "").lower())
    ]
    day_trades = [
        e for e in events
        if e["event"] in {"SHADOW_DAY_TRADE_SIGNAL", "SHADOW_FAST_SIGNAL"}
        or (e["score"] >= DAY_TRADE_THRESHOLD and "fast" in e["event"])
    ]
    skips = [e for e in events if "SKIP" in e["event"]]
    return {
        "total_events": len(events),
        "event_counts": dict(counts),
        "top_symbols": symbols.most_common(10),
        "paper_68_plus_decisions": len(paper_decisions),
        "paper_70_plus_decisions": len([e for e in paper_decisions if e["score"] >= 70]),
        "small_cap_68_plus_signals": len(small_cap),
        "day_trade_80_plus_signals": len(day_trades),
        "skip_events": len(skips),
        "latest_events": latest,
    }


def simulate_small_cap(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    signals = [e for e in events if e["event"] == "SHADOW_SMALL_CAP_BUY_DECISION"]
    symbol_counts = Counter(e["symbol"] for e in signals)
    avg_score = round(sum(e["score"] for e in signals) / len(signals), 2) if signals else 0
    suggested_slots = min(SMALL_CAP_MAX_POSITIONS, len(symbol_counts))
    estimated_capital_used = min(SMALL_CAP_STARTING_CASH, suggested_slots * SMALL_CAP_MAX_POSITION)
    return {
        "mode": "shadow_only",
        "starting_cash": SMALL_CAP_STARTING_CASH,
        "max_position": SMALL_CAP_MAX_POSITION,
        "max_positions": SMALL_CAP_MAX_POSITIONS,
        "signals": len(signals),
        "unique_symbols": len(symbol_counts),
        "avg_score": avg_score,
        "estimated_slots_used": suggested_slots,
        "estimated_capital_used": estimated_capital_used,
        "top_symbols": symbol_counts.most_common(8),
        "note": "Read-only eligibility simulation. PnL requires future price/outcome tracking.",
    }


def simulate_day_trade(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    signals = [e for e in events if e["event"] in {"SHADOW_DAY_TRADE_SIGNAL", "SHADOW_FAST_SIGNAL"}]
    confirmed = [e for e in signals if "confirmed" in str(e.get("rotation_decision", "")).lower()]
    unconfirmed = [e for e in signals if "unconfirmed" in str(e.get("rotation_decision", "")).lower()]
    avg_score = round(sum(e["score"] for e in signals) / len(signals), 2) if signals else 0
    return {
        "mode": "shadow_only_aggressive",
        "threshold": DAY_TRADE_THRESHOLD,
        "signals": len(signals),
        "confirmed_signals": len(confirmed),
        "unconfirmed_signals": len(unconfirmed),
        "avg_score": avg_score,
        "latest_signals": signals[-10:],
        "note": "Day-trade shadow is intentionally medium/high risk and research-only until outcome data proves edge.",
    }


def simulate_paper(events: List[Dict[str, Any]], trades: List[Dict[str, str]]) -> Dict[str, Any]:
    paper_signals = [e for e in events if e["event"] == "LEARNING_SHADOW_BUY_DECISION" and e["score"] >= PAPER_THRESHOLD]
    trade_summary = summarize_trade_history(trades)
    avg_score = round(sum(e["score"] for e in paper_signals) / len(paper_signals), 2) if paper_signals else 0
    return {
        "mode": "paper_learning",
        "threshold": PAPER_THRESHOLD,
        "signals": len(paper_signals),
        "avg_signal_score": avg_score,
        "trade_history": trade_summary,
        "latest_signals": paper_signals[-10:],
    }


def setup_performance(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"events": 0, "scores": [], "symbols": Counter()})
    for e in events:
        setup = setup_from_reason(e.get("reason", ""), e.get("notes", ""))
        grouped[setup]["events"] += 1
        grouped[setup]["scores"].append(e.get("score", 0))
        if e.get("symbol") and e.get("symbol") != "-":
            grouped[setup]["symbols"][e["symbol"]] += 1
    out = {}
    for setup, data in grouped.items():
        scores = data["scores"]
        out[setup] = {
            "events": data["events"],
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "top_symbols": data["symbols"].most_common(5),
        }
    return out


def scanner_snapshot(rows: List[Dict[str, str]], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "scanner_rows": len(rows),
        "top_candidate_count": len(candidates),
        "latest_top_candidates": candidates[:10],
    }


def build_outputs() -> Dict[str, Any]:
    events = learning_events()
    trades = trade_rows()
    scanner = scanner_rows()
    candidates = latest_top_candidates()
    generated_at = utc_now()
    learning_summary = summarize_learning(events)
    paper = simulate_paper(events, trades)
    small_cap = simulate_small_cap(events)
    day_trade = simulate_day_trade(events)
    setup_stats = setup_performance(events)
    scanner_stats = scanner_snapshot(scanner, candidates)
    forward = {
        "generated_at": generated_at,
        "mode": "read_only_simulation",
        "paper": paper,
        "small_cap": small_cap,
        "day_trade": day_trade,
        "learning_summary": learning_summary,
        "scanner": scanner_stats,
        "notes": [
            "This simulator reads logs and research artifacts only.",
            "It does not import bot.py, place orders, or change trade logic.",
            "PnL quality improves as more paper/shadow outcomes are logged.",
        ],
    }
    backtest = {
        "generated_at": generated_at,
        "mode": "bot_logic_output_backtest_placeholder",
        "status": "collecting_real_bot_outputs",
        "paper_threshold": PAPER_THRESHOLD,
        "small_cap_threshold": SMALL_CAP_THRESHOLD,
        "day_trade_threshold": DAY_TRADE_THRESHOLD,
        "trade_history": summarize_trade_history(trades),
        "learning_summary": learning_summary,
        "note": "This summarizes bot output data until enough outcomes exist for true score-based backtesting.",
    }
    setup_output = {
        "generated_at": generated_at,
        "mode": "setup_performance_from_shadow_logs",
        "setups": setup_stats,
    }
    return {"forward": forward, "backtest": backtest, "setup_performance": setup_output}


def main() -> Dict[str, Any]:
    outputs = build_outputs()
    write_json(FORWARD_SIM_OUT, outputs["forward"])
    write_json(BACKTEST_OUT, outputs["backtest"])
    write_json(SETUP_PERFORMANCE_OUT, outputs["setup_performance"])
    return {
        "status": "ok",
        "generated_at": outputs["forward"]["generated_at"],
        "wrote": [str(FORWARD_SIM_OUT), str(BACKTEST_OUT), str(SETUP_PERFORMANCE_OUT)],
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
