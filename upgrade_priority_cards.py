from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_priority").write_text(text)

ADD = r'''

// === PRIORITY CARD EMPHASIS ===
(function(){
  function enhance(){
    document.querySelectorAll("div").forEach(el=>{
      const txt = el.innerText || "";

      if(txt.includes("Portfolio Value") || txt.includes("Open P/L")){
        el.style.border = "1px solid rgba(120,255,180,.35)";
        el.style.boxShadow = "0 0 30px rgba(120,255,180,.12)";
      }
    });
  }

  enhance();
  setInterval(enhance, 3000);
})();
'''

if "PRIORITY CARD EMPHASIS" not in text:
    p.write_text(text + ADD)
    print("✅ Priority cards upgraded")
