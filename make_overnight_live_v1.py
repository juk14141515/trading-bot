from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_overnight_live_v1").write_text(text)

ADD = r'''

// === OVERNIGHT LIVE REFRESH V1 ===
window.addEventListener("load", function () {
  if (window.__overnightLiveRefreshV1) return;
  window.__overnightLiveRefreshV1 = true;

  async function refreshOvernightIfOpen() {
    const panel = document.getElementById("ponderOvernightPanel");
    if (!panel) return;
    if (getComputedStyle(panel).display === "none") return;

    const btn = document.getElementById("ponderOvernightBtn");
    if (!btn) return;

    // Re-click to reload panel content without page refresh.
    panel.style.display = "none";
    btn.click();
  }

  setInterval(refreshOvernightIfOpen, 60000);
});
'''

if "OVERNIGHT LIVE REFRESH V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Overnight live refresh installed")
else:
    print("Already installed")
