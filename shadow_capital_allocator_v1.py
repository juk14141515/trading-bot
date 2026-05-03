import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
ROTATION = OUT / "rotation_engine_latest.json"
DEST = OUT / "shadow_capital_allocator_latest.json"

def load_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

def allocation_size(confidence, action, rotation_score):
    if "ROTATE NOW" in action and confidence == "High":
        return 0.25
    if "WATCH" in action and confidence in ["High", "Medium"] and rotation_score >= 65:
        return 0.10
    if "LOW EDGE" in action:
        return 0.00
    return 0.00

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rotation = load_json(ROTATION)
    suggestions = rotation.get("rotation_suggestions", [])

    shadow_actions = []

    for r in suggestions[:25]:
        action = r.get("action", "")
        confidence = r.get("confidence", "Low")
        rotation_score = float(r.get("rotation_score", 0))
        size = allocation_size(confidence, action, rotation_score)

        if size <= 0:
            recommendation = "NO SHADOW MOVE"
        elif size <= 0.10:
            recommendation = "SHADOW SMALL ROTATION"
        else:
            recommendation = "SHADOW STANDARD ROTATION"

        shadow_actions.append({
            "timestamp": now,
            "sell_symbol": r.get("sell_symbol"),
            "buy_symbol": r.get("buy_symbol"),
            "shadow_allocation_pct": size,
            "recommendation": recommendation,
            "confidence": confidence,
            "action": action,
            "rotation_score": rotation_score,
            "expected_edge": r.get("expected_edge"),
            "status": "shadow_only",
            "note": "This is a simulated allocation recommendation only. No live orders are placed."
        })

    active = [x for x in shadow_actions if x["shadow_allocation_pct"] > 0]

    payload = {
        "updated_at": now,
        "version": "shadow_allocator_v1",
        "status": "shadow_only",
        "shadow_actions": shadow_actions,
        "top_shadow_action": active[0] if active else {},
        "summary": {
            "actions_checked": len(shadow_actions),
            "shadow_moves": len(active),
            "total_shadow_allocation_pct": round(sum(x["shadow_allocation_pct"] for x in active), 2),
        },
        "notes": [
            "Shadow allocator does not touch the live bot.",
            "It estimates how much capital would rotate if the system were enabled.",
            "Use this to compare future hypothetical allocations against real bot results."
        ]
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
