from pathlib import Path

files = ["web_dashboard.py", "profit_ops_routes.py", "profit_lab_routes.py"]

CSS = """
/* === PONDER EXACT UI RESTORE V1 === */

/* Hide only the duplicate bottom-right AI Health badge */
#ponder_ai_health_badge {
  display: none !important;
}

/* Ensure settings + dock are visible above layout */
.pp-gear,
.pp-tool-dock,
#ppToolDock {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 99999 !important;
}

/* Gear should be a round button */
.pp-gear {
  position: fixed !important;
  right: 22px !important;
  bottom: 26px !important;
}

/* Dock sits above gear */
.pp-tool-dock,
#ppToolDock {
  position: fixed !important;
  right: 22px !important;
  top: 260px !important;
  flex-direction: column !important;
}

/* === END PONDER EXACT UI RESTORE V1 === */
"""

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()
    p.with_suffix(p.suffix + ".bak_exact_ui_restore_v1").write_text(text)

    if "PONDER EXACT UI RESTORE V1" not in text:
        text = text.replace("</style>", CSS + "\n</style>", 1)

    p.write_text(text)
    print(f"✅ Patched {file}")

print("DONE")
