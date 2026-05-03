from pathlib import Path

files = ["web_dashboard.py", "profit_ops_routes.py", "profit_lab_routes.py"]

CSS = """
/* === PONDER PRO MOTION POLISH V1 === */

/* Soft animated background glow */
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(circle at 22% 15%, rgba(125,255,150,0.12), transparent 28%),
    radial-gradient(circle at 80% 20%, rgba(120,150,255,0.10), transparent 30%),
    radial-gradient(circle at 45% 90%, rgba(120,255,210,0.06), transparent 35%);
  animation: ponderGlow 9s ease-in-out infinite alternate;
}

@keyframes ponderGlow {
  from { opacity: 0.65; transform: scale(1); }
  to { opacity: 1; transform: scale(1.03); }
}

/* Keep actual UI above glow */
body > * {
  position: relative;
  z-index: 1;
}

/* Card entrance + hover */
.card, .metric-card, .panel {
  animation: ponderCardIn 0.45s ease both;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.card:hover, .metric-card:hover, .panel:hover {
  transform: translateY(-3px);
  border-color: rgba(130,255,160,0.35) !important;
  box-shadow: 0 16px 42px rgba(0,0,0,0.32);
}

@keyframes ponderCardIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Live pulse chips */
.pill, .badge, .chip {
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.pill:hover, .badge:hover, .chip:hover {
  transform: translateY(-1px);
}

/* Market/open/live pulse */
.pill:first-child,
.badge:first-child,
.chip:first-child {
  animation: ponderPulse 2.4s ease-in-out infinite;
}

@keyframes ponderPulse {
  0%, 100% { box-shadow: 0 0 0 rgba(130,255,160,0); }
  50% { box-shadow: 0 0 22px rgba(130,255,160,0.18); }
}

/* Better active sidebar feel */
a[href="/"],
a[href="/profit"],
a[href="/profit-lab"],
a[href="/history"],
a[href="/logout"] {
  transition: transform 0.16s ease, background 0.16s ease, border-color 0.16s ease;
}

a[href="/"]:hover,
a[href="/profit"]:hover,
a[href="/profit-lab"]:hover,
a[href="/history"]:hover,
a[href="/logout"]:hover {
  transform: translateX(3px);
}

/* Fun Ponder paw ambience near title */
h1::after {
  content: "  🐾";
  font-size: 0.55em;
  opacity: 0.7;
  display: inline-block;
  animation: ponderPawFloat 3.5s ease-in-out infinite;
}

@keyframes ponderPawFloat {
  0%, 100% { transform: translateY(0) rotate(-5deg); opacity: 0.55; }
  50% { transform: translateY(-5px) rotate(6deg); opacity: 0.9; }
}

/* Respect users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}

/* === END PONDER PRO MOTION POLISH V1 === */
"""

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()
    p.with_suffix(p.suffix + ".bak_motion_polish_v1").write_text(text)

    if "PONDER PRO MOTION POLISH V1" not in text:
        text = text.replace("</style>", CSS + "\n</style>", 1)

    p.write_text(text)
    print(f"✅ Motion polish added to {file}")

print("DONE")
