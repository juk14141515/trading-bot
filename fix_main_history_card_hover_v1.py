from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_main_history_hover_v1").write_text(text)

ADD = r'''

// === MAIN + HISTORY CARD HOVER FIX V1 ===
window.addEventListener("load", function () {
  if (window.__mainHistoryCardHoverV1) return;
  window.__mainHistoryCardHoverV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    body .card {
      transition:
        transform .18s ease,
        box-shadow .18s ease,
        border-color .18s ease,
        background .18s ease !important;
      will-change: transform;
    }

    body .card:hover {
      transform: translateY(-5px) scale(1.01) !important;
      border-color: rgba(124,255,178,.38) !important;
      box-shadow:
        0 22px 60px rgba(0,0,0,.48),
        0 0 30px rgba(124,255,178,.18) !important;
      background:
        radial-gradient(circle at top left, rgba(124,255,178,.08), transparent 34%),
        rgba(18,24,45,.92) !important;
    }

    body .card .big,
    body .card .value {
      transition: text-shadow .18s ease, color .18s ease !important;
    }

    body .card:hover .big,
    body .card:hover .value {
      text-shadow: 0 0 18px rgba(124,255,178,.22) !important;
    }

    body table tr {
      transition: background .16s ease !important;
    }

    body table tr:hover {
      background: rgba(124,255,178,.06) !important;
    }

    body.pp-motion-off .card,
    body.pp-motion-off .card:hover,
    body.pp-motion-off table tr {
      transition: none !important;
      transform: none !important;
    }
  `;
  document.head.appendChild(style);
});
'''

if "MAIN + HISTORY CARD HOVER FIX V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Main + History card hover fixed")
else:
    print("Already installed")
