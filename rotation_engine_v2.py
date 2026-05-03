import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

SCANNER = OUT / "market_intelligence_latest.json"
SELL = OUT / "sell_intelligence_latest.json"
DEST = OUT / "rotation_engine_latest.json"
PERF_LOG = OUT / "rotation_suggestions_log.jsonl"

def load_json(path):
    return json.loads(path.read_text()) if path.exists() else {}

def score_rotation(sell_item, buy_item):
    sell_pressure = float(sell_item.get("sell_pressure", 0))
    buy_score = float(buy_item.get("final_score", 0))
    entry_score = float(buy_item.get("entry_score", 50))
    expected_edge = buy_score - sell_pressure

    if buy_score < sell_pressure:
        return None

    base = (
        sell_pressure * 0.40 +
        buy_score * 0.40 +
        entry_score * 0.15 +
        expected_edge * 0.25
    )
    return round(max(0, min(100, base)), 2)

def action_label(rotation_score, sell_pressure, expected_edge):
    if rotation_score >= 65 and sell_pressure >= 55 and expected_edge >= 10:
        return "🔴 ROTATE NOW"
    if rotation_score >= 60 and sell_pressure >= 50:
        return "🟠 WATCH ROTATION"
    if rotation_score >= 55:
        return "🟡 LOW EDGE"
    return "⚪ IGNORE"

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scanner = load_json(SCANNER)
    sell = load_json(SELL)

    trade_ready = scanner.get("trade_ready", [])
    sell_candidates = sell.get("sell_candidates", [])
    suggestions = []

    for s in sell_candidates:
        sell_pressure = float(s.get("sell_pressure", 0))
        if sell_pressure < 45:
            continue

        for b in trade_ready[:12]:
            sell_symbol = s.get("symbol")
            buy_symbol = b.get("symbol")

            if not sell_symbol or not buy_symbol or sell_symbol == buy_symbol:
                continue

            buy_score = float(b.get("final_score", 0))
            entry_score = float(b.get("entry_score", 50))
            expected_edge = round(buy_score - sell_pressure, 2)
            rotation_score = score_rotation(s, b)

            if rotation_score is None:
                continue

            action = action_label(rotation_score, sell_pressure, expected_edge)

            suggestions.append({
                "timestamp": now,
                "sell_symbol": sell_symbol,
                "buy_symbol": buy_symbol,
                "rotation_score": rotation_score,
                "action": action,
                "expected_edge": expected_edge,
                "sell_pressure": sell_pressure,
                "sell_verdict": s.get("verdict"),
                "buy_score": buy_score,
                "entry_score": entry_score,
                "entry_zone": b.get("entry_zone"),
                "buy_label": b.get("label"),
                "status": "research_only",
                "why": [
                    f"{sell_symbol} sell pressure is {sell_pressure}/100",
                    f"{buy_symbol} scanner score is {buy_score}",
                    f"Expected edge is {expected_edge}",
                    f"{buy_symbol} entry zone: {b.get('entry_zone')}",
                ],
            })

    suggestions = sorted(suggestions, key=lambda x: x["rotation_score"], reverse=True)
    top = suggestions[0] if suggestions else {}

    payload = {
        "updated_at": now,
        "version": "v2",
        "status": "research_only",
        "rotation_suggestions": suggestions[:25],
        "top_rotation": top,
        "summary": {
            "sell_candidates_checked": len(sell_candidates),
            "trade_ready_checked": len(trade_ready),
            "rotations_found": len(suggestions),
            "rotate_now_count": len([x for x in suggestions if "ROTATE NOW" in x["action"]]),
            "watch_count": len([x for x in suggestions if "WATCH" in x["action"]]),
        },
        "notes": [
            "Rotation Engine v2 is research-only.",
            "ROTATE NOW means high sell pressure plus stronger replacement candidate.",
            "Do not connect to live bot until performance tracker proves rotations are useful."
        ],
    }

    DEST.write_text(json.dumps(payload, indent=2))
    archive = OUT / f"rotation_engine_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    archive.write_text(json.dumps(payload, indent=2))

    with PERF_LOG.open("a") as f:
        for item in suggestions[:10]:
            f.write(json.dumps(item) + "\n")

    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
