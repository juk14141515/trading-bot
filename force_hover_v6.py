from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_v6").write_text(text)

ADDON = r'''

// === PONDER FORCE HOVER V6 (DIRECT TARGET) ===
(function () {
  if (window.__ponderHoverV6) return;
  window.__ponderHoverV6 = true;

  function apply() {

    const cards = Array.from(document.querySelectorAll("div"))
      .filter(el => {
        const txt = el.innerText || "";
        return (
          txt.includes("Portfolio Value") ||
          txt.includes("Buying Power") ||
          txt.includes("Open P/L") ||
          txt.includes("Win Rate") ||
          txt.includes("Capital Deployed") ||
          txt.includes("Scanner Events") ||
          txt.includes("Account Status")
        );
      });

    cards.forEach(card => {

      if (card.dataset.hoverBound) return;
      card.dataset.hoverBound = "1";

      card.style.transition = "all .2s ease";

      card.addEventListener("mouseenter", () => {
        card.style.transform = "translateY(-8px)";
        card.style.boxShadow =
          "0 25px 60px rgba(0,0,0,.5), 0 0 30px rgba(120,255,180,.25)";
      });

      card.addEventListener("mouseleave", () => {
        card.style.transform = "translateY(0)";
        card.style.boxShadow = "";
      });

    });
  }

  apply();
  setInterval(apply, 2000);

})();
'''

if "PONDER FORCE HOVER V6" not in text:
    p.write_text(text + ADDON)
    print("✅ V6 hover injected")
else:
    print("Already installed")
