from pathlib import Path

files = [
    "web_dashboard.py",
    "profit_ops_routes.py",
    "profit_lab_routes.py"
]

CSS = """
/* === PONDER PRO KILL AI HEALTH BUBBLE V3 === */

/* Kill ANY element that contains AI Health in bottom overlay style */
div:has(span),
div:has(a) {
}

/* More precise: hide floating AI health card by content */
div:has(> a[href*="profit"]),
div:has(> a[href*="dashboard"]) {
    display: none !important;
}

/* Fallback: hide small bottom-right floating cards */
div {
}

/* Specific override if class-based */
.ai-health,
.aiHealth,
.health-widget,
.healthWidget {
    display: none !important;
}

/* === END FIX === */
"""

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()
    backup = p.with_suffix(p.suffix + ".bak_ai_health_v3")
    backup.write_text(text)

    if "KILL AI HEALTH BUBBLE V3" in text:
        print(f"Already applied to {file}")
        continue

    if "</style>" in text:
        text = text.replace("</style>", CSS + "\n</style>", 1)
    else:
        text = text.replace("</head>", f"<style>{CSS}</style>\n</head>", 1)

    p.write_text(text)
    print(f"✅ AI Health bubble removed from {file}")

print("DONE")
