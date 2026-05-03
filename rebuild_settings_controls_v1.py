from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_rebuild_settings_controls_v1").write_text(text)

old = '''panel.innerHTML = "<h3>🐾 Ponder Pro Settings</h3><p>Focus Mode: Ready</p><p>Colorblind Mode: Icons + labels</p><p>Theme: Default</p>";'''

new = '''panel.innerHTML = `
  <h3 style="margin-top:0">🐾 Ponder Pro Settings</h3>
  <button data-pp-toggle="focus" style="width:100%;margin:6px 0;padding:10px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);color:white;cursor:pointer">Focus Mode</button>
  <button data-pp-toggle="contrast" style="width:100%;margin:6px 0;padding:10px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);color:white;cursor:pointer">High Contrast</button>
  <button data-pp-toggle="motion" style="width:100%;margin:6px 0;padding:10px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);color:white;cursor:pointer">Reduce Motion</button>
  <button data-pp-toggle="black" style="width:100%;margin:6px 0;padding:10px;border-radius:12px;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);color:white;cursor:pointer">True Black Theme</button>
`;'''

if old not in text:
    print("Old settings block not found. No changes made.")
else:
    text = text.replace(old, new)

    add = r'''
// === PONDER SETTINGS CONTROLS V1 ===
window.addEventListener("load", function () {
  if (window.__ponderSettingsControlsV1) return;
  window.__ponderSettingsControlsV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    body.pp-focus .pp-card-hover:not(:hover) { opacity: .82; }
    body.pp-contrast { filter: contrast(1.08) brightness(1.04); }
    body.pp-motion-off *, body.pp-motion-off *::before, body.pp-motion-off *::after {
      animation: none !important;
      transition: none !important;
    }
    body.pp-black {
      background: #000 !important;
    }
    body.pp-black .globalSidebar {
      background: #030303 !important;
    }
    body.pp-black .card,
    body.pp-black .pp-card-hover,
    body.pp-black section,
    body.pp-black .intel-card {
      background: rgba(5,5,8,.96) !important;
      border-color: rgba(120,255,180,.18) !important;
    }
  `;
  document.head.appendChild(style);

  const map = {
    focus: "pp-focus",
    contrast: "pp-contrast",
    motion: "pp-motion-off",
    black: "pp-black"
  };

  Object.values(map).forEach(cls => {
    if (localStorage.getItem(cls) === "1") document.body.classList.add(cls);
  });

  document.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-pp-toggle]");
    if (!btn) return;

    const key = btn.getAttribute("data-pp-toggle");
    const cls = map[key];
    if (!cls) return;

    const on = !document.body.classList.contains(cls);
    document.body.classList.toggle(cls, on);
    localStorage.setItem(cls, on ? "1" : "0");
  });
});
'''
    if "PONDER SETTINGS CONTROLS V1" not in text:
        text += "\n" + add + "\n"

    p.write_text(text)
    print("✅ Settings controls rebuilt")
