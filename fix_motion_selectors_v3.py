from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_motion_selectors_v3").write_text(text)

ADDON = r'''

// === PONDER MOTION SELECTORS V3 ===
(function () {
  if (window.__ponderMotionSelectorsV3) return;
  window.__ponderMotionSelectorsV3 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    .ponder-card-live {
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, opacity .25s ease !important;
    }
    .ponder-card-live:hover {
      transform: translateY(-4px) !important;
      box-shadow: 0 18px 42px rgba(0,0,0,.35), 0 0 24px rgba(124,255,178,.18) !important;
      border-color: rgba(124,255,178,.35) !important;
    }
    .ponder-card-enter {
      animation: ponderCardEnter .38s ease forwards;
    }
    @keyframes ponderCardEnter {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  document.head.appendChild(style);

  function looksLikeCard(el) {
    if (!el || el === document.body) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 160 || r.height < 90) return false;

    const txt = (el.innerText || "").trim();
    if (!txt) return false;

    const style = window.getComputedStyle(el);
    const hasBorder = style.borderStyle !== "none" && style.borderWidth !== "0px";
    const rounded = parseFloat(style.borderRadius || "0") > 8;
    const darkBox = style.backgroundColor && style.backgroundColor !== "rgba(0, 0, 0, 0)";

    return hasBorder || rounded || darkBox;
  }

  function applyMotion() {
    document.querySelectorAll("main div, .container div, body > div div").forEach((el, i) => {
      if (!looksLikeCard(el)) return;
      if (el.closest(".globalSidebar")) return;
      if (el.id === "ppToolDock" || el.id === "ppSettingsPanel") return;

      el.classList.add("ponder-card-live");

      if (!el.dataset.ponderEnterV3) {
        el.dataset.ponderEnterV3 = "1";
        el.classList.add("ponder-card-enter");
        el.style.animationDelay = Math.min(i * 25, 350) + "ms";
      }
    });
  }

  applyMotion();
  setInterval(applyMotion, 3000);
})();
'''

if "PONDER MOTION SELECTORS V3" not in text:
    p.write_text(text.rstrip() + "\n" + ADDON + "\n")
    print("✅ Added motion selectors v3")
else:
    print("Already installed")

print("DONE")
