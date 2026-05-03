from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_blackout_theme_v1").write_text(text)

ADD = r'''

// === PONDER BLACKOUT THEME V1 ===
window.addEventListener("load", function () {
  if (window.__ponderBlackoutThemeV1) return;
  window.__ponderBlackoutThemeV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    body.ponder-theme-blackout {
      background:
        radial-gradient(circle at 20% 10%, rgba(90,255,140,.07), transparent 28%),
        linear-gradient(135deg, #020409 0%, #05070d 45%, #010208 100%) !important;
      color: #f4f7ff !important;
    }

    body.ponder-theme-blackout .globalSidebar {
      background: #03050b !important;
      border-right: 1px solid rgba(255,255,255,.06) !important;
    }

    body.ponder-theme-blackout div {
      border-color: rgba(255,255,255,.08);
    }

    body.ponder-theme-blackout .premium-card,
    body.ponder-theme-blackout .pp-card-hover {
      background: linear-gradient(180deg, rgba(12,16,28,.96), rgba(5,7,13,.98)) !important;
      border-color: rgba(255,255,255,.08) !important;
    }

    body.ponder-theme-blackout .premium-card:hover,
    body.ponder-theme-blackout .pp-card-hover:hover {
      border-color: rgba(130,255,170,.30) !important;
      box-shadow: 0 18px 45px rgba(0,0,0,.55), 0 0 18px rgba(130,255,170,.12) !important;
    }

    body.ponder-theme-blackout h1 span,
    body.ponder-theme-blackout h1,
    body.ponder-theme-blackout .positive {
      text-shadow: none !important;
    }

    .ponder-theme-btn {
      width: 100%;
      margin-top: 10px;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid rgba(140,160,255,.25);
      background: rgba(255,255,255,.06);
      color: white;
      cursor: pointer;
      font-weight: 800;
      text-align: left;
    }

    .ponder-theme-btn:hover {
      background: rgba(255,255,255,.10);
    }
  `;
  document.head.appendChild(style);

  function applyTheme(theme) {
    document.body.classList.remove("ponder-theme-blackout");
    if (theme === "blackout") document.body.classList.add("ponder-theme-blackout");
    localStorage.setItem("ponderTheme", theme);
  }

  applyTheme(localStorage.getItem("ponderTheme") || "default");

  setTimeout(() => {
    const panel = document.getElementById("ppSettingsPanel");
    if (!panel || document.getElementById("ponderThemeControls")) return;

    const controls = document.createElement("div");
    controls.id = "ponderThemeControls";
    controls.innerHTML = `
      <hr style="border:0;border-top:1px solid rgba(255,255,255,.12);margin:14px 0">
      <div style="font-size:13px;color:#b8c2d8;margin-bottom:6px">Theme</div>
      <button class="ponder-theme-btn" id="ponderDefaultTheme">Default</button>
      <button class="ponder-theme-btn" id="ponderBlackoutTheme">Blackout</button>
    `;
    panel.appendChild(controls);

    document.getElementById("ponderDefaultTheme").onclick = () => applyTheme("default");
    document.getElementById("ponderBlackoutTheme").onclick = () => applyTheme("blackout");
  }, 400);
});
'''

if "PONDER BLACKOUT THEME V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Blackout theme installed")
else:
    print("Already installed")
