from pathlib import Path

files = ["web_dashboard.py", "profit_ops_routes.py", "profit_lab_routes.py"]

CSS = """
/* === PONDER PRO VISUAL CLEANUP CSS V1 === */

/* Hide duplicate bottom-right AI health bubble without removing logic */
div[style*="position:fixed"][style*="bottom"][style*="right"],
div[style*="position: fixed"][style*="bottom"][style*="right"] {
  display: none !important;
}

/* Hide right-side floating dock buttons visually only */
.pp-floating-dock,
.floating-dock,
.quickDock,
#quickDock,
button[style*="position:fixed"],
button[style*="position: fixed"] {
  display: none !important;
}

/* Give content more breathing room */
.card, .panel, .metric-card {
  border-radius: 22px !important;
}

/* Keep command/status pills readable */
.badge, .pill, .chip {
  letter-spacing: 0.2px;
}

/* === END PONDER PRO VISUAL CLEANUP CSS V1 === */
"""

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()
    backup = p.with_suffix(p.suffix + ".bak_visual_cleanup_css_v1")
    backup.write_text(text)

    if "PONDER PRO VISUAL CLEANUP CSS V1" not in text:
        text = text.replace("</style>", CSS + "\n</style>", 1)

    p.write_text(text)
    print(f"✅ Visual cleanup CSS added to {file}")

print("DONE")
