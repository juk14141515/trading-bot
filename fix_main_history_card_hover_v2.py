from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_main_history_hover_v2").write_text(text)

ADD = r'''

// === MAIN + HISTORY CARD HOVER FIX V2 (FORCED OVERRIDE) ===
window.addEventListener("load", function () {
  if (window.__mainHistoryCardHoverV2) return;
  window.__mainHistoryCardHoverV2 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    html body .card {
      transition:
        transform .18s ease,
        box-shadow .18s ease,
        border-color .18s ease,
        background .18s ease !important;
    }

    html body .card:hover {
      transform: translateY(-6px) scale(1.015) !important;
      border: 1px solid rgba(124,255,178,.5) !important;
      box-shadow:
        0 30px 80px rgba(0,0,0,.6),
        0 0 40px rgba(124,255,178,.25) !important;

      background:
        radial-gradient(circle at top left, rgba(124,255,178,.12), transparent 40%),
        rgba(15,20,40,.95) !important;
    }

    html body .card:hover h3 {
      color: #7cffb2 !important;
    }

    html body .card:hover .big,
    html body .card:hover .value {
      text-shadow: 0 0 20px rgba(124,255,178,.35) !important;
    }

    html body table tr:hover {
      background: rgba(124,255,178,.08) !important;
    }

    html body.pp-motion-off .card,
    html body.pp-motion-off .card:hover {
      transform: none !important;
      transition: none !important;
    }
  `;
  document.head.appendChild(style);

  console.log("🔥 Main + History hover FIX V2 loaded");
});
'''

if "MAIN + HISTORY CARD HOVER FIX V2" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Installed V2 hover fix")
else:
    print("Already installed")
