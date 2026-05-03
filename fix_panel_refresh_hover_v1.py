from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_panel_refresh_hover_v1").write_text(text)

ADD = r'''

// === PANEL REFRESH + HOVER FIX V1 ===
window.addEventListener("load", function () {
  if (window.__panelRefreshHoverFixV1) return;
  window.__panelRefreshHoverFixV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    body.pp-panel-open .card:hover,
    body.pp-panel-open .pp-card-hover:hover,
    body.pp-panel-open section:hover,
    body.pp-panel-open table:hover {
      transform: none !important;
      box-shadow: none !important;
      border-color: inherit !important;
    }

    body.pp-panel-open .card::before,
    body.pp-panel-open .pp-card-hover::before {
      opacity: 0 !important;
    }

    #ponderLearningPanel,
    #ponderIntelPanel,
    #ponderMarketIntelPanel,
    #ppSettingsPanel {
      backdrop-filter: blur(14px);
    }
  `;
  document.head.appendChild(style);

  const panels = [
    "ponderLearningPanel",
    "ponderIntelPanel",
    "ponderMarketIntelPanel",
    "ppSettingsPanel"
  ];

  function getOpenPanel() {
    return panels.find(id => {
      const el = document.getElementById(id);
      return el && el.style.display !== "none" && getComputedStyle(el).display !== "none";
    });
  }

  function syncPanelState() {
    const open = getOpenPanel();
    document.body.classList.toggle("pp-panel-open", !!open);
    if (open) localStorage.setItem("ponder_open_panel", open);
  }

  setInterval(syncPanelState, 500);

  document.addEventListener("click", function () {
    setTimeout(syncPanelState, 50);
  });

  window.addEventListener("beforeunload", function () {
    const open = getOpenPanel();
    if (open) localStorage.setItem("ponder_open_panel", open);
    else localStorage.removeItem("ponder_open_panel");
  });

  // Reopen the last panel after refresh
  setTimeout(function () {
    const wanted = localStorage.getItem("ponder_open_panel");
    if (!wanted) return;

    const panel = document.getElementById(wanted);
    if (!panel) return;

    if (wanted === "ponderLearningPanel") {
      const btn = document.getElementById("ponderLearningBtn");
      if (btn) btn.click();
    } else if (wanted === "ponderIntelPanel") {
      const btn = document.getElementById("ponderIntelBtn");
      if (btn) btn.click();
    } else if (wanted === "ponderMarketIntelPanel") {
      const btns = Array.from(document.querySelectorAll("button"));
      const b = btns.find(x => (x.title || "").includes("Market Intelligence") && x.id !== "ponderIntelBtn");
      if (b) b.click();
    } else if (wanted === "ppSettingsPanel") {
      const btn = document.getElementById("ppSettingsButton");
      if (btn) btn.click();
    }

    document.body.classList.add("pp-panel-open");
  }, 900);

  // When close buttons are clicked, do not reopen after refresh.
  document.addEventListener("click", function(e) {
    const txt = (e.target.innerText || "").trim().toLowerCase();
    if (txt === "close") {
      localStorage.removeItem("ponder_open_panel");
      setTimeout(() => document.body.classList.remove("pp-panel-open"), 100);
    }
  });
});
'''

if "PANEL REFRESH + HOVER FIX V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Panel refresh + hover fix installed")
else:
    print("Already installed")
