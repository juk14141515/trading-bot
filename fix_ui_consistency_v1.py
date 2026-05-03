from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_ui_consistency_v1").write_text(text)

ADD = r'''

// === PONDER UI CONSISTENCY FIX V1 ===
window.addEventListener("load", function () {
  if (window.__ponderUIConsistencyV1) return;
  window.__ponderUIConsistencyV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    /* Keep settings/intel panels above all visual modes */
    #ppSettingsPanel,
    #ppSettingsButton,
    #ponderIntelBtn,
    #ponderIntelPanel,
    #ponderMarketIntelPanel,
    #ppToolDock {
      filter: none !important;
      opacity: 1 !important;
      visibility: visible !important;
    }

    /* Better contrast mode without hiding overlays */
    body.pp-contrast {
      filter: none !important;
    }

    body.pp-contrast .card,
    body.pp-contrast .pp-card-hover,
    body.pp-contrast section,
    body.pp-contrast table,
    body.pp-contrast .intel-card {
      border-color: rgba(150, 255, 190, .36) !important;
      box-shadow: 0 0 0 1px rgba(150,255,190,.08), 0 18px 45px rgba(0,0,0,.45) !important;
    }

    /* Premium cohesion for Main + History + older route cards */
    .container > div,
    .container section,
    .content > div,
    .content section,
    main > div,
    main section {
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
    }

    .container > div:hover,
    .container section:hover,
    .content > div:hover,
    .content section:hover,
    main > div:hover,
    main section:hover {
      transform: translateY(-3px) !important;
      box-shadow: 0 20px 55px rgba(0,0,0,.42), 0 0 24px rgba(124,255,178,.14) !important;
      border-color: rgba(124,255,178,.28) !important;
    }

    /* History table polish */
    table {
      overflow: hidden;
      border-radius: 16px;
    }

    tr {
      transition: background .15s ease !important;
    }

    tr:hover {
      background: rgba(124,255,178,.055) !important;
    }

    /* Make settings buttons obviously interactive */
    #ppSettingsPanel button {
      display: block !important;
      cursor: pointer !important;
      transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease !important;
    }

    #ppSettingsPanel button:hover {
      transform: translateY(-2px);
      border-color: rgba(124,255,178,.45) !important;
      box-shadow: 0 0 18px rgba(124,255,178,.18);
    }
  `;
  document.head.appendChild(style);

  function retagMoreCards() {
    const candidates = Array.from(document.querySelectorAll("div, section, table"));
    candidates.forEach(el => {
      if (el.closest(".globalSidebar")) return;
      if (el.closest("#ppSettingsPanel")) return;
      if (el.closest("#ponderIntelPanel")) return;
      if (el.closest("#ponderMarketIntelPanel")) return;
      if (el.id === "ppToolDock" || el.id === "ppSettingsButton") return;

      const r = el.getBoundingClientRect();
      if (r.width < 220 || r.height < 90) return;
      if (r.width > window.innerWidth * 0.92) return;

      const txt = (el.innerText || "").trim();
      const looksLikeCard =
        txt.includes("Portfolio") ||
        txt.includes("Buying Power") ||
        txt.includes("Open P/L") ||
        txt.includes("Equity") ||
        txt.includes("History") ||
        txt.includes("Snapshot") ||
        txt.includes("Account") ||
        txt.includes("Win Rate") ||
        txt.includes("Bot Actions") ||
        txt.includes("Scanner") ||
        txt.includes("Rotations");

      if (looksLikeCard) el.classList.add("pp-card-hover");
    });
  }

  retagMoreCards();
  setInterval(retagMoreCards, 2500);

  // If a mode ever hides settings accidentally, force it back visible when gear clicked.
  document.addEventListener("click", function(e) {
    if (e.target && e.target.id === "ppSettingsButton") {
      setTimeout(() => {
        const panel = document.getElementById("ppSettingsPanel");
        if (panel) {
          panel.style.opacity = "1";
          panel.style.visibility = "visible";
          panel.style.filter = "none";
        }
      }, 50);
    }
  });
});
'''

if "PONDER UI CONSISTENCY FIX V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ UI consistency fix installed")
else:
    print("Already installed")
