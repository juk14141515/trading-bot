from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_v5").write_text(text)

ADDON = r'''

// === PONDER FORCE HOVER V5 (NO CSS DEPENDENCY) ===
(function () {
  if (window.__ponderForceHoverV5) return;
  window.__ponderForceHoverV5 = true;

  function isCard(el) {
    if (!el) return false;

    const r = el.getBoundingClientRect();

    if (r.width < 220 or r.height < 120) return false;

    const style = getComputedStyle(el);

    return (
      style.backgroundColor !== "rgba(0, 0, 0, 0)" ||
      style.borderRadius !== "0px"
    );
  }

  function apply() {
    document.querySelectorAll("div").forEach(el => {

      if (!isCard(el)) return;

      if (el.closest(".globalSidebar")) return;
      if (el.id === "ppToolDock") return;

      if (el.dataset.hoverBound) return;
      el.dataset.hoverBound = "1";

      // smooth base transition
      el.style.transition = "all .18s ease";

      el.addEventListener("mouseenter", () => {
        el.style.transform = "translateY(-6px)";
        el.style.boxShadow = "0 20px 55px rgba(0,0,0,.45), 0 0 28px rgba(120,255,180,.22)";
      });

      el.addEventListener("mouseleave", () => {
        el.style.transform = "translateY(0)";
        el.style.boxShadow = "";
      });

      // entrance animation (once)
      if (!el.dataset.entered) {
        el.dataset.entered = "1";
        el.style.opacity = "0";
        el.style.transform = "translateY(14px)";

        setTimeout(() => {
          el.style.transition = "all .35s ease";
          el.style.opacity = "1";
          el.style.transform = "translateY(0)";
        }, 30);
      }

    });
  }

  apply();
  setInterval(apply, 2500);

})();
'''

if "PONDER FORCE HOVER V5" not in text:
    p.write_text(text + ADDON)
    print("✅ Force hover V5 injected")
else:
    print("Already installed")
