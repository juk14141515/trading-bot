from pathlib import Path

SNAP = Path("system_snapshot.py")
SNAP.with_suffix(".py.backup_decision_fix_v1").write_text(SNAP.read_text())

text = SNAP.read_text()

text = text.replace(
'''    decision_list = decisions.get("decisions", [])
    top = decision_list[0] if decision_list else {}''',
'''    decision_list = (
        decisions.get("decisions") or
        decisions.get("candidates") or
        decisions.get("data") or
        []
    )

    # Sort strongest setup first
    try:
        decision_list = sorted(
            decision_list,
            key=lambda x: float(x.get("score", 0) or 0),
            reverse=True
        )
    except Exception:
        pass

    top = decision_list[0] if decision_list else {}'''
)

SNAP.write_text(text)
print("✅ Fixed decision parsing + sorting in system_snapshot.py")
