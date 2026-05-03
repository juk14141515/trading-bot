from pathlib import Path

p = Path("web_dashboard.py")
text = p.read_text()

backup = p.with_suffix(".py.bak_runtime_ui_loader_v1")
backup.write_text(text)

BLOCK = r'''
# === PONDER RUNTIME UI LOADER V1 ===
@app.after_request
def ponder_runtime_ui_loader(response):
    try:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return response

        html = response.get_data(as_text=True)

        if "PONDER_RUNTIME_UI_LOADER_V1" in html:
            return response

        ui = """
<!-- PONDER_RUNTIME_UI_LOADER_V1 -->
<script>
window.addEventListener("load", function () {
  if (!document.getElementById("ppToolDock")) {
    var dock = document.createElement("div");
    dock.id = "ppToolDock";
    dock.style.cssText = "position:fixed;right:22px;top:260px;z-index:99999;display:flex;flex-direction:column;gap:12px;";
    dock.innerHTML =
      '<button title="Top">⬆️</button>' +
      '<button title="Refresh">🔄</button>' +
      '<button title="Copy Link">📋</button>';

    var buttons = dock.querySelectorAll("button");
    buttons[0].onclick = function(){ window.scrollTo({top:0, behavior:"smooth"}); };
    buttons[1].onclick = function(){ location.reload(); };
    buttons[2].onclick = function(){ navigator.clipboard.writeText(location.href); };

    buttons.forEach(function(btn){
      btn.style.cssText = "width:44px;height:44px;border-radius:14px;border:1px solid rgba(140,160,255,.35);background:rgba(18,24,45,.9);color:white;cursor:pointer;font-size:18px;";
    });

    document.body.appendChild(dock);
  }

  if (!document.getElementById("ppSettingsButton")) {
    var gear = document.createElement("button");
    gear.id = "ppSettingsButton";
    gear.innerHTML = "⚙️";
    gear.title = "Ponder Pro Settings";
    gear.style.cssText = "position:fixed;right:22px;bottom:24px;z-index:100000;width:52px;height:52px;border-radius:50%;border:1px solid rgba(140,160,255,.4);background:rgba(18,24,45,.95);color:white;cursor:pointer;font-size:22px;";

    var panel = document.createElement("div");
    panel.id = "ppSettingsPanel";
    panel.style.cssText = "display:none;position:fixed;right:22px;bottom:88px;z-index:100000;width:280px;padding:18px;border-radius:18px;border:1px solid rgba(140,160,255,.35);background:rgba(18,24,45,.96);color:white;box-shadow:0 18px 45px rgba(0,0,0,.35);font-family:Arial,sans-serif;";
    panel.innerHTML =
      '<h3 style="margin:0 0 10px">🐾 Ponder Pro Settings</h3>' +
      '<div style="font-size:13px;color:#b8c2d8">Focus Mode: Ready</div>' +
      '<div style="font-size:13px;color:#b8c2d8">Colorblind Mode: Icons + labels</div>' +
      '<div style="font-size:13px;color:#b8c2d8">Theme: Default</div>';

    gear.onclick = function(){
      panel.style.display = panel.style.display === "none" ? "block" : "none";
    };

    document.body.appendChild(panel);
    document.body.appendChild(gear);
  }
});
</script>
"""

        if "</body>" in html:
            html = html.replace("</body>", ui + "</body>")
        else:
            html += ui

        response.set_data(html)
        response.headers["Content-Length"] = str(len(response.get_data()))
        return response
    except Exception:
        return response
# === END PONDER RUNTIME UI LOADER V1 ===
'''

if "PONDER RUNTIME UI LOADER V1" in text:
    print("Already installed")
else:
    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, BLOCK + "\n\n" + marker)
    else:
        text += "\n\n" + BLOCK + "\n"

    p.write_text(text)
    print("✅ Runtime UI loader injected into web_dashboard.py")
