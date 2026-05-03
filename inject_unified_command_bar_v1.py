from pathlib import Path
import re

files = ["web_dashboard.py", "profit_ops_routes.py", "profit_lab_routes.py"]

CSS = r"""
/* === PONDER PRO UNIFIED COMMAND BAR V1 === */
.pp-command-bar,
.globalCommandBar,
.command-bar,
#ppCommandBar {
  position: fixed !important;
  top: 18px !important;
  right: 24px !important;
  z-index: 9999 !important;
  display: flex !important;
  gap: 10px !important;
  align-items: center !important;
  padding: 10px 14px !important;
  border-radius: 999px !important;
  background: rgba(12, 16, 32, 0.82) !important;
  border: 1px solid rgba(140, 160, 255, 0.25) !important;
  backdrop-filter: blur(14px) !important;
  box-shadow: 0 10px 30px rgba(0,0,0,0.28) !important;
}

.pp-command-bar span,
.globalCommandBar span,
.command-bar span,
#ppCommandBar span {
  font-weight: 800 !important;
  color: #f5f7ff !important;
}

.pp-command-chip {
  padding: 6px 11px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
  white-space: nowrap;
}

.pp-live-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #88ff99;
  display: inline-block;
  box-shadow: 0 0 12px #88ff99;
}

/* Remove noisy right-side floating dock buttons */
.pp-floating-dock,
.floating-dock,
.quickDock,
#quickDock {
  display: none !important;
}

/* Mobile: keep bar readable */
@media (max-width: 800px) {
  .pp-command-bar,
  .globalCommandBar,
  .command-bar,
  #ppCommandBar {
    position: static !important;
    margin: 12px 16px !important;
    flex-wrap: wrap !important;
    border-radius: 18px !important;
  }
}
/* === END PONDER PRO UNIFIED COMMAND BAR V1 === */
"""

BAR = r"""
<div id="ppCommandBar" class="pp-command-bar">
  <span class="pp-live-dot"></span>
  <span class="pp-command-chip">LIVE</span>
  <span class="pp-command-chip">Market: --</span>
  <span class="pp-command-chip">Health: 100/100</span>
  <span class="pp-command-chip">P/L: --</span>
</div>
"""

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()

    # backup
    backup = p.with_suffix(p.suffix + ".bak_command_bar_v1")
    backup.write_text(text)

    # inject CSS before </style>
    if "PONDER PRO UNIFIED COMMAND BAR V1" not in text:
        text = text.replace("</style>", CSS + "\n</style>", 1)

    # remove duplicate command bar divs if obvious
    text = re.sub(r'<div[^>]*(?:globalCommandBar|ppCommandBar|command-bar)[^>]*>.*?</div>', "", text, flags=re.DOTALL)

    # inject one command bar after body
    if 'id="ppCommandBar"' not in text:
        text = text.replace("<body>", "<body>\n" + BAR, 1)

    p.write_text(text)
    print(f"✅ Unified command bar patched: {file}")

print("DONE")
