from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_livepl").write_text(text)

ADD = r'''

// === LIVE P/L PULSE ===
(function(){
  function pulsePL(){
    document.querySelectorAll("div").forEach(el=>{
      if((el.innerText||"").includes("Open P/L")){
        const val = el.querySelector("*");
        if(!val) return;

        val.style.transition="all .4s ease";
        val.style.textShadow="0 0 10px rgba(120,255,180,.4)";

        setTimeout(()=>{
          val.style.textShadow="0 0 20px rgba(120,255,180,.7)";
        },200);

        setTimeout(()=>{
          val.style.textShadow="";
        },800);
      }
    });
  }

  setInterval(pulsePL, 2500);
})();
'''

if "LIVE P/L PULSE" not in text:
    p.write_text(text + ADD)
    print("✅ Live P/L pulse added")
else:
    print("Already added")
