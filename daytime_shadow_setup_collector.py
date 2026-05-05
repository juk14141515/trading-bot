"""Daytime shadow setup collector for Ponder Invest AI.

Research-only. Reads the bot/scanner's latest candidate artifact and appends
opportunities into research_data/shadow_setups.csv using shadow_setup_logger.

This module never imports bot.py, never calls Alpaca order endpoints, and never
places trades. It exists only to capture daytime opportunities so the overnight
research pipeline can analyze what the system saw but may not have traded.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from shadow_setup_logger import log_shadow_setups_from_candidates

ROOT = Path(__file__).resolve().parent
TOP_CANDIDATES = ROOT / "top_10_candidates_v2.json"
BOT_STATUS = ROOT / "bot_status.json"
LOG_DIR = ROOT / "logs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def extract_candidates(raw: Any) -> List[Dict[str, Any]]:
    """Normalize likely top_10_candidates_v2.json shapes into candidate dicts."""
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict):
        candidates = []
        for key in ("candidates", "top_candidates", "scanner_top", "items", "rows", "data"):
            value = raw.get(key)
            if isinstance(value, list):
                candidates = value
                break
    else:
        candidates = []

    normalized: List[Dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol") or item.get("ticker") or item.get("asset")
        if not symbol:
            continue
        score = (
            item.get("score")
            or item.get("final_score")
            or item.get("confidence")
            or item.get("total")
            or 0
        )
        normalized.append({
            "symbol": str(symbol).upper(),
            "score": safe_float(score),
            "trend": item.get("trend") or item.get("market_trend") or item.get("label") or "unknown",
            "analyst": safe_float(item.get("analyst") or item.get("analyst_score") or 0),
            "news": safe_float(item.get("news") or item.get("news_score") or 0),
            "entry_price": item.get("entry_price") or item.get("price") or item.get("last_price") or "",
            "reason": item.get("reason") or item.get("summary") or item.get("thesis") or "daytime candidate artifact",
        })
    return normalized


def market_regime() -> str:
    status = read_json(BOT_STATUS, {})
    return str(
        status.get("market_trend")
        or status.get("trading_state")
        or status.get("why_not_trading")
        or "unknown"
    )[:80]


def main() -> Dict[str, Any]:
    raw = read_json(TOP_CANDIDATES, [])
    candidates = extract_candidates(raw)
    logged = log_shadow_setups_from_candidates(
        candidates,
        market_regime=market_regime(),
        source="daytime_top_candidates_shadow",
    )
    result = {
        "status": "ok",
        "mode": "research_only_daytime_shadow_collection",
        "timestamp": utc_now(),
        "source": str(TOP_CANDIDATES),
        "candidates_seen": len(candidates),
        "setups_logged": logged,
        "note": "Read-only collector. No live trading logic touched.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
