from pathlib import Path

files = [
    "web_dashboard.py",
    "profit_ops_routes.py",
    "profit_lab_routes.py"
]

CSS = """
/* === PONDER PRO SAFE VISUAL CLEANUP V2 === */

/* Hide bottom-right duplicate AI Health bubble only */
div[style*="position: fixed"][style*="bottom"][style*="right"][style*="z-index"],
div[style*="position:fixed"][style*="bottom"][style*="right"][style*="z-index"] {
    display: none !important;
}

/* Hide right-side floating icon dock only */
button[style*="position: fixed"][style*="right"],
button[style*="position:fixed"][style*="right"],
a[style*="position: fixed"][style*="right"],
a[style*="position:fixed"][style*="right"] {
    display: none !important;
}

/* Safer visual polish */
.card,
.metric-card,
.panel {
    border-radius: 22px !important;
}

.card:hover,
.metric-card:hover,
.panel:hover {
    transform: translateY(-2px);
    transition: 0.18s ease;
}

/* Keep readable contrast */
body {
    text-rendering: optimizeLegibility;
}

/* === END PONDER PRO SAFE VISUAL CLEANUP V2 === */
"""

for file in files:
    p = Path(file)
    if not p.exists():
        print(f"SKIP missing {file}")
        continue

    text = p.read_text()
    backup = p.with_suffix(p.suffix + ".bak_safe_visual_cleanup_v2")
    backup.write_text(text)

    if "PONDER PRO SAFE VISUAL CLEANUP V2" in text:
        print(f"Already installed in {file}")
        continue

    if "</style>" in text:
        text = text.replace("</style>", CSS + "\n</style>", 1)
    else:
        text = text.replace("</head>", f"<style>{CSS}</style>\n</head>", 1)

    p.write_text(text)
    print(f"✅ Added safe visual cleanup to {file}")

print("DONE")
