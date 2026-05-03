from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_calm_motion_v2").write_text(text)

ADDON = r'''

// === PONDER CALM MOTION V2 ===
(function () {
  if (window.__ponderCalmMotionV2) return;
  window.__ponderCalmMotionV2 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    .card, .metric-card, .panel, canvas {
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, opacity .25s ease !important;
    }

    .card:hover, .metric-card:hover, .panel:hover {
      transform: translateY(-3px) !important;
      box-shadow: 0 18px 42px rgba(0,0,0,.35), 0 0 28px rgba(124,255,178,.18) !important;
      border-color: rgba(124,255,178,.38) !important;
    }

    .ponder-enter {
      opacity: 0;
      transform: translateY(10px);
      animation: ponderEnter .38s ease forwards;
    }

    @keyframes ponderEnter {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(style);

  function applyMotion() {
    document.querySelectorAll(".card, .metric-card, .panel").forEach((el, i) => {
      if (!el.dataset.ponderEnter) {
        el.dataset.ponderEnter = "1";
        el.classList.add("ponder-enter");
        el.style.animationDelay = Math.min(i * 45, 400) + "ms";
      }
    });
  }

  applyMotion();
  setTimeout(applyMotion, 500);
})();
'''

if "PONDER CALM MOTION V2" not in text:
    p.write_text(text.rstrip() + "\n" + ADDON + "\n")
    print("✅ Added calm motion v2")
else:
    print("Already installed")
