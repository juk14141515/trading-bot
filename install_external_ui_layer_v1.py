from pathlib import Path

ROOT = Path(".")
WEB = ROOT / "web_dashboard.py"
BACKUP = ROOT / "web_dashboard.py.bak_full_ponder_pro_v3_20260501_175409"

# 1. Restore clean dashboard first
if BACKUP.exists():
    WEB.write_text(BACKUP.read_text())
    print("✅ Restored clean web_dashboard.py")
else:
    print("⚠️ Backup not found. Using current web_dashboard.py")

# 2. Create static UI file
static_dir = ROOT / "static"
static_dir.mkdir(exist_ok=True)

ui_js = static_dir / "ponder_ui.js"
ui_js.write_text(r'''
window.addEventListener("load", function () {
  console.log("Ponder external UI loaded");

  if (!document.getElementById("ppToolDock")) {
    const dock = document.createElement("div");
    dock.id = "ppToolDock";
    dock.style.cssText = `
      position:fixed;
      right:22px;
      top:260px;
      z-index:99999;
      display:flex;
      flex-direction:column;
      gap:12px;
    `;

    dock.innerHTML = `
      <button title="Top">⬆️</button>
      <button title="Refresh">🔄</button>
      <button title="Copy Link">📋</button>
    `;

    const buttons = dock.querySelectorAll("button");
    buttons[0].onclick = () => window.scrollTo({top:0, behavior:"smooth"});
    buttons[1].onclick = () => location.reload();
    buttons[2].onclick = () => navigator.clipboard.writeText(location.href);

    buttons.forEach(btn => {
      btn.style.cssText = `
        width:44px;
        height:44px;
        border-radius:14px;
        border:1px solid rgba(140,160,255,.35);
        background:rgba(18,24,45,.9);
        color:white;
        cursor:pointer;
        font-size:18px;
      `;
    });

    document.body.appendChild(dock);
  }

  if (!document.getElementById("ppSettingsButton")) {
    const gear = document.createElement("button");
    gear.id = "ppSettingsButton";
    gear.innerHTML = "⚙️";
    gear.title = "Ponder Pro Settings";
    gear.style.cssText = `
      position:fixed;
      right:22px;
      bottom:24px;
      z-index:100000;
      width:52px;
      height:52px;
      border-radius:50%;
      border:1px solid rgba(140,160,255,.4);
      background:rgba(18,24,45,.95);
      color:white;
      cursor:pointer;
      font-size:22px;
    `;

    const panel = document.createElement("div");
    panel.id = "ppSettingsPanel";
    panel.style.cssText = `
      display:none;
      position:fixed;
      right:22px;
      bottom:88px;
      z-index:100000;
      width:290px;
      padding:18px;
      border-radius:18px;
      border:1px solid rgba(140,160,255,.35);
      background:rgba(18,24,45,.96);
      color:white;
      box-shadow:0 18px 45px rgba(0,0,0,.35);
      font-family:Arial,sans-serif;
    `;

    panel.innerHTML = `
      <h3 style="margin:0 0 10px">🐾 Ponder Pro Settings</h3>
      <div style="font-size:13px;color:#b8c2d8">✅ Focus Mode: Ready</div>
      <div style="font-size:13px;color:#b8c2d8">✅ Colorblind Mode: Icons + labels</div>
      <div style="font-size:13px;color:#b8c2d8">✅ Theme: Default</div>
    `;

    gear.onclick = () => {
      panel.style.display = panel.style.display === "none" ? "block" : "none";
    };

    document.body.appendChild(panel);
    document.body.appendChild(gear);
  }

  document.querySelectorAll(".card").forEach((card, i) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(10px)";
    setTimeout(() => {
      card.style.transition = "all .35s ease";
      card.style.opacity = "1";
      card.style.transform = "translateY(0)";
    }, i * 45);
  });
});
''')
print("✅ Created static/ponder_ui.js")

# 3. Add safe Flask after_request loader
text = WEB.read_text()

block = r'''
# === PONDER EXTERNAL UI LOADER V1 ===
@app.after_request
def ponder_external_ui_loader(response):
    try:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return response

        html = response.get_data(as_text=True)
        tag = '<script src="/static/ponder_ui.js"></script>'

        if tag not in html:
            if "</body>" in html:
                html = html.replace("</body>", tag + "\n</body>")
            else:
                html += tag

            response.set_data(html)
            response.headers["Content-Length"] = str(len(response.get_data()))

        return response
    except Exception:
        return response
# === END PONDER EXTERNAL UI LOADER V1 ===
'''

if "PONDER EXTERNAL UI LOADER V1" not in text:
    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, block + "\n\n" + marker)
    else:
        text += "\n\n" + block + "\n"
    WEB.write_text(text)
    print("✅ Added external UI loader to web_dashboard.py")
else:
    print("Already installed")

print("DONE")
