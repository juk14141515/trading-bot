from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_v4").write_text(text)

ADDON = r'''

// === PONDER UI MOTION V4 (FORCE APPLY) ===
(function () {
  if (window.__ponderMotionV4) return;
  window.__ponderMotionV4 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    .pp-live-card {
      transition: transform .18s ease, box-shadow .18s ease !important;
    }

    .pp-live-card:hover {
      transform: translateY(-5px) !important;
      box-shadow:
        0 20px 50px rgba(0,0,0,.4),
        0 0 25px rgba(120,255,180,.2) !important;
    }
  `;
  document.head.appendChild(style);

  function isCard(el) {
    if (!el) return false;

    const r = el.getBoundingClientRect();

    // size filter (your cards are big)
    if (r.width < 200 || r.height < 120) return false;

    const style = getComputedStyle(el);

    // must look like a UI box
    const hasVisual =
      style.borderRadius !== "0px" ||
      style.backgroundColor !== "rgba(0, 0, 0, 0)" ||
      style.boxShadow !== "none";

    return hasVisual;
  }

  function apply() {
    document.querySelectorAll("div").forEach(el => {
      if (!isCard(el)) return;

      // ignore sidebar
      if (el.closest(".globalSidebar")) return;

      // ignore floating UI
      if (el.id === "ppToolDock") return;

      el.classList.add("pp-live-card");
    });
  }

  apply();
  setInterval(apply, 3000);
})();
'''

if "PONDER UI MOTION V4" not in text:
    p.write_text(text + ADDON)
    print("✅ Motion V4 injected (force mode)")
else:
    print("Already installed")
