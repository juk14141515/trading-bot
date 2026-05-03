from pathlib import Path

# 1) Force ponder_ui.js onto every HTML response from web_dashboard.py
p = Path("web_dashboard.py")
text = p.read_text()
p.with_suffix(".py.bak_global_ui_loader_calm_v1").write_text(text)

HOOK = r'''

# === GLOBAL PONDER UI LOADER V1 ===
@app.after_request
def inject_ponder_ui_global(response):
    try:
        if response.mimetype == "text/html":
            html = response.get_data(as_text=True)
            script = '<script src="/static/ponder_ui.js?v=globalcalm1"></script>'
            if "/static/ponder_ui.js" not in html:
                if "</body>" in html:
                    html = html.replace("</body>", script + "\n</body>")
                elif "</html>" in html:
                    html = html.replace("</html>", script + "\n</html>")
                else:
                    html += script
                response.set_data(html)
    except Exception:
        pass
    return response
'''

if "GLOBAL PONDER UI LOADER V1" not in text:
    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, HOOK + "\n" + marker)
    else:
        text += "\n" + HOOK
    p.write_text(text)
    print("✅ Added global UI loader to web_dashboard.py")
else:
    print("Global UI loader already present")


# 2) Add calm hover override at very end of ponder_ui.js
js = Path("static/ponder_ui.js")
ui = js.read_text()
js.with_suffix(".js.bak_calm_hover_v1").write_text(ui)

CALM = r'''

// === CALM PREMIUM HOVER OVERRIDE V1 ===
window.addEventListener("load", function () {
  if (window.__calmPremiumHoverV1) return;
  window.__calmPremiumHoverV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    html body .card,
    html body .pp-card-hover {
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
    }

    html body .card:hover,
    html body .pp-card-hover:hover {
      transform: translateY(-2px) !important;
      border-color: rgba(124,255,178,.30) !important;
      box-shadow:
        0 14px 36px rgba(0,0,0,.38),
        0 0 14px rgba(124,255,178,.12) !important;
      background: rgba(18,24,45,.92) !important;
    }

    html body .card:hover h2,
    html body .card:hover h3,
    html body .card:hover .big,
    html body .card:hover .value {
      text-shadow: 0 0 10px rgba(124,255,178,.16) !important;
    }

    html body.pp-motion-off .card:hover,
    html body.pp-motion-off .pp-card-hover:hover {
      transform: none !important;
      box-shadow: none !important;
    }
  `;
  document.head.appendChild(style);
});
'''

if "CALM PREMIUM HOVER OVERRIDE V1" not in ui:
    js.write_text(ui.rstrip() + "\n" + CALM + "\n")
    print("✅ Added calm hover override")
else:
    print("Calm hover already present")
