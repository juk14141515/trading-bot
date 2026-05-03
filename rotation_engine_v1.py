import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

SCANNER = OUT / "market_intelligence_latest.json"
SELL = OUT / "sell_intelligence_latest.json"
DEST = OUT / "rotation_engine_latest.json"


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def score_rotation(sell_item, buy_item):
    sell_pressure = float(sell_item.get("sell_pressure", 0))
    buy_score = float(buy_item.get("final_score", 0))
    entry_score = float(buy_item.get("entry_score", 50))

    sell_component = sell_pressure * 0.45
    buy_component = buy_score * 0.40
    entry_component = entry_score * 0.15

    return round(sell_component + buy_component + entry_component, 2)


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    scanner = load_json(SCANNER)
    sell = load_json(SELL)

    trade_ready = scanner.get("trade_ready", [])
    sell_candidates = sell.get("sell_candidates", [])

    suggestions = []

    for s in sell_candidates:
        sell_pressure = float(s.get("sell_pressure", 0))

        if sell_pressure < 50:
            continue

        for b in trade_ready[:10]:
            sell_symbol = s.get("symbol")
            buy_symbol = b.get("symbol")

            if not sell_symbol or not buy_symbol:
                continue

            if sell_symbol == buy_symbol:
                continue

            rotation_score = score_rotation(s, b)

            if rotation_score >= 70:
                action = "🔴 Rotate Candidate"
            elif rotation_score >= 60:
                action = "🟠 Watch Rotation"
            else:
                action = "🟡 Weak Rotation"

            suggestions.append({
                "sell_symbol": sell_symbol,
                "buy_symbol": buy_symbol,
                "rotation_score": rotation_score,
                "action": action,
                "sell_pressure": s.get("sell_pressure"),
                "sell_verdict": s.get("verdict"),
                "buy_score": b.get("final_score"),
                "entry_zone": b.get("entry_zone"),
                "buy_label": b.get("label"),
                "why": [
                    f"{sell_symbol} sell pressure is {s.get('sell_pressure')}/100",
                    f"{buy_symbol} scanner score is {b.get('final_score')}",
                    f"{buy_symbol} entry zone: {b.get('entry_zone')}",
                ],
            })

    suggestions = sorted(suggestions, key=lambda x: x["rotation_score"], reverse=True)

    payload = {
        "updated_at": now,
        "status": "research_only",
        "rotation_suggestions": suggestions[:20],
        "top_rotation": suggestions[0] if suggestions else {},
        "summary": {
            "sell_candidates_checked": len(sell_candidates),
            "trade_ready_checked": len(trade_ready),
            "rotations_found": len(suggestions),
        },
        "notes": [
            "Research-only rotation engine. Does not place trades.",
            "This connects weak holdings/sell pressure to stronger scanner candidates.",
            "Next step: compare suggestions against actual next-day outcomes before connecting to bot."
        ],
    }

    DEST.write_text(json.dumps(payload, indent=2))

    archive = OUT / f"rotation_engine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    archive.write_text(json.dumps(payload, indent=2))

    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
