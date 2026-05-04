"""Research-only strategy evaluator for Ponder Invest AI.

This module never places orders and never imports bot.py. It reads existing
trade/research artifacts, produces honest strategy summaries, and writes JSON
feeds consumed by the dashboard.
"""

from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RESEARCH_DIR = ROOT / "static" / "research"
TRADE_HISTORY = ROOT / "trade_history.csv"
BACKTEST_OUTPUT = RESEARCH_DIR / "current_strategy_backtest_latest.json"
FORWARD_OUTPUT = RESEARCH_DIR / "forward_setup_simulations_latest.json"
ROTATION_PERFORMANCE = RESEARCH_DIR / "rotation_performance_latest.json"
MARKET_INTELLIGENCE = RESEARCH_DIR / "market_intelligence_latest.json"
CAPITAL_INTELLIGENCE = RESEARCH_DIR / "capital_intelligence_latest.json"

SETUPS = ["current_bot", "breakout", "pullback", "momentum", "oversold", "rotation"]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    os.replace(tmp, path)


def read_trade_history() -> List[Dict[str, Any]]:
    if not TRADE_HISTORY.exists():
        return []
    try:
        with TRADE_HISTORY.open(newline="", errors="ignore") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def closed_trade_rows(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    closed: List[Dict[str, Any]] = []
    for row in rows:
        action = str(row.get("action") or row.get("side") or "").upper()
        pnl = safe_float(row.get("pnl"), None)
        pnl_pct = safe_float(row.get("pnl_pct"), None)
        if action == "SELL" and (pnl is not None or pnl_pct is not None):
            enriched = dict(row)
            enriched["_pnl"] = pnl
            enriched["_pnl_pct"] = pnl_pct
            closed.append(enriched)
    return closed


def summarize_closed_trades(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "status": "insufficient_data",
            "sample_size": 0,
            "message": "No closed trades with PnL were found. Strategy metrics will stay disabled until real outcomes exist.",
        }

    returns = [r.get("_pnl_pct") for r in rows if isinstance(r.get("_pnl_pct"), (int, float))]
    pnl_values = [r.get("_pnl") for r in rows if isinstance(r.get("_pnl"), (int, float))]
    wins = [r for r in rows if (r.get("_pnl") or 0) > 0 or (r.get("_pnl_pct") or 0) > 0]
    losses = [r for r in rows if (r.get("_pnl") or 0) < 0 or (r.get("_pnl_pct") or 0) < 0]

    by_symbol: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_symbol[str(row.get("symbol") or "UNKNOWN")].append(row)

    symbol_rows = []
    for symbol, symbol_trades in sorted(by_symbol.items()):
        symbol_wins = [r for r in symbol_trades if (r.get("_pnl") or 0) > 0 or (r.get("_pnl_pct") or 0) > 0]
        symbol_pnl = sum(r.get("_pnl") or 0 for r in symbol_trades)
        symbol_returns = [r.get("_pnl_pct") for r in symbol_trades if isinstance(r.get("_pnl_pct"), (int, float))]
        symbol_rows.append(
            {
                "symbol": symbol,
                "sample_size": len(symbol_trades),
                "win_rate": round((len(symbol_wins) / len(symbol_trades)) * 100, 2) if symbol_trades else None,
                "net_pnl": round(symbol_pnl, 2),
                "avg_return_pct": round((sum(symbol_returns) / len(symbol_returns)) * 100, 4) if symbol_returns else None,
            }
        )

    return {
        "status": "evaluated",
        "sample_size": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round((len(wins) / len(rows)) * 100, 2),
        "net_pnl": round(sum(pnl_values), 2) if pnl_values else None,
        "avg_return_pct": round((sum(returns) / len(returns)) * 100, 4) if returns else None,
        "best_return_pct": round(max(returns) * 100, 4) if returns else None,
        "worst_return_pct": round(min(returns) * 100, 4) if returns else None,
        "by_symbol": sorted(symbol_rows, key=lambda r: r.get("sample_size", 0), reverse=True)[:20],
    }


def setup_placeholder(setup: str, reason: str) -> Dict[str, Any]:
    return {
        "setup": setup,
        "status": "insufficient_data",
        "sample_size": 0,
        "win_rate": None,
        "avg_return_pct": None,
        "outcome": "insufficient data",
        "reason": reason,
    }


def build_backtest_feed() -> Dict[str, Any]:
    trades = closed_trade_rows(read_trade_history())
    summary = summarize_closed_trades(trades)
    reason = "No closed trade rows with PnL were available."
    setups = [setup_placeholder(setup, reason) for setup in SETUPS]

    if summary.get("status") == "evaluated":
        setups[0] = {
            "setup": "current_bot",
            "status": "evaluated",
            "sample_size": summary.get("sample_size"),
            "win_rate": summary.get("win_rate"),
            "avg_return_pct": summary.get("avg_return_pct"),
            "outcome": "real closed trade memory",
            "reason": "Derived only from closed trade_history.csv rows with PnL.",
        }

    return {
        "updated_at": iso_now(),
        "version": "research_only_strategy_evaluator_v1",
        "status": summary.get("status"),
        "source": "trade_history.csv",
        "summary": summary,
        "setups": setups,
        "limitations": [
            "No live orders are placed by this module.",
            "No fake strategy edge is generated when real outcomes are missing.",
            "Historical setup comparison requires enough logged closed trades or separately generated forward simulation outcomes.",
        ],
    }


def build_forward_feed() -> Dict[str, Any]:
    rotation_perf = read_json(ROTATION_PERFORMANCE)
    market = read_json(MARKET_INTELLIGENCE)
    capital = read_json(CAPITAL_INTELLIGENCE)

    rotation_summary = rotation_perf.get("summary") or {}
    evaluated = safe_float(rotation_summary.get("evaluated"), 0) or 0
    pending = safe_float(rotation_summary.get("pending_evaluations"), 0) or 0

    if evaluated <= 0:
        status = "insufficient_data"
        message = "No evaluated forward/shadow outcomes were found yet. Keep collecting simulated ideas before trusting setup win rates."
    else:
        status = "evaluated"
        message = "Forward/shadow outcomes are available for comparison."

    setup_rows = [setup_placeholder(setup, message) for setup in SETUPS]
    if evaluated > 0:
        setup_rows[-1] = {
            "setup": "rotation",
            "status": "evaluated",
            "sample_size": int(evaluated),
            "win_rate": rotation_summary.get("win_rate"),
            "avg_return_pct": rotation_summary.get("avg_alpha"),
            "outcome": "rotation performance feed",
            "reason": "Derived from rotation_performance_latest.json.",
        }

    scanner_top = market.get("scanner_top") or []

    return {
        "updated_at": iso_now(),
        "version": "research_only_forward_setup_summary_v1",
        "status": status,
        "summary": {
            "evaluated": int(evaluated),
            "pending": int(pending),
            "message": message,
            "scanner_candidates_available": len(scanner_top),
            "capital_snapshot_available": bool(capital),
        },
        "setups": setup_rows,
        "notes": [
            "This feed summarizes evaluated research outcomes only.",
            "It does not infer win rates from scanner scores.",
            "Use this as the display layer until a dedicated forward_setup_simulator logs enough real simulated outcomes.",
        ],
    }


def run() -> Dict[str, Any]:
    backtest = build_backtest_feed()
    forward = build_forward_feed()
    write_json(BACKTEST_OUTPUT, backtest)
    write_json(FORWARD_OUTPUT, forward)
    return {"backtest": backtest, "forward": forward}


if __name__ == "__main__":
    output = run()
    print("Ponder strategy evaluator complete")
    print(f"backtest status: {output['backtest'].get('status')}")
    print(f"forward status: {output['forward'].get('status')}")
    print(f"wrote: {BACKTEST_OUTPUT}")
    print(f"wrote: {FORWARD_OUTPUT}")
