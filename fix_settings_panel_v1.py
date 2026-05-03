from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_settings_fix_v1").write_text(text)

ADD = r'''

// === PONDER SETTINGS FIX V1 ===
window.addEventListener("load", function () {
  if (window.__ponderSettingsFixV1) return;
  window.__ponderSettingsFixV1 = true;

  function applySetting(name, on) {
    document.body.classList.toggle(name, on);
    localStorage.setItem(name, on ? "1" : "0");
  }

  function restoreSettings() {
    ["ponder-focus", "ponder-colorblind", "ponder-contrast", "ponder-reduced-motion"].forEach(cls => {
      if (localStorage.getItem(cls) === "1") document.body.classList.add(cls);
    });
  }

  restoreSettings();

  const style = document.createElement("style");
  style.innerHTML = `
    body.ponder-focus .card,
    body.ponder-focus .intel-card {
      box-shadow: none !important;
    }

    body.ponder-contrast {
      filter: contrast(1.08);
    }

    body.ponder-reduced-motion * {
      animation: none !important;
      transition: none !important;
    }

    body.ponder-colorblind .positive,
    body.ponder-colorblind .value {
      text-decoration: underline;
    }

    #ppSettingsPanel button {
      cursor: pointer !important;
    }
  `;
  document.head.appendChild(style);

  function fixPanel() {
    const panel = document.getElementById("ppSettingsPanel");
    if (!panel) return;

    const buttons = Array.from(panel.querySelectorAll("button"));

    buttons.forEach(btn => {
      const label = (btn.innerText || "").toLowerCase();

      btn.onclick = function () {
        if (label.includes("focus")) {
          applySetting("ponder-focus", !document.body.classList.contains("ponder-focus"));
        } else if (label.includes("colorblind")) {
          applySetting("ponder-colorblind", !document.body.classList.contains("ponder-colorblind"));
        } else if (label.includes("contrast")) {
          applySetting("ponder-contrast", !document.body.classList.contains("ponder-contrast"));
        } else if (label.includes("animation")) {
          applySetting("ponder-reduced-motion", !document.body.classList.contains("ponder-reduced-motion"));
        } else if (label.includes("refresh") || label.includes("now")) {
          location.reload();
        }
      };
    });
  }

  setTimeout(fixPanel, 500);
  setInterval(fixPanel, 3000);
});
'''

if "PONDER SETTINGS FIX V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Settings panel fixed")
else:
    print("Already installed")
