
(function(){
  if(window.PonderV2) return;

  const P = {
    version: "pondermod2",
    isLogin: location.pathname === "/login" || location.pathname.startsWith("/login"),
    async json(path){
      const res = await fetch(path + "?ts=" + Date.now(), {cache:"no-store"});
      if(!res.ok) throw new Error(path + " " + res.status);
      return await res.json();
    },
    safe(v, fallback="—"){
      return (v === undefined || v === null || v === "" || Number.isNaN(v)) ? fallback : v;
    },
    esc(v){
      return String(v ?? "").replace(/[&<>"']/g, c => ({
        "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
      }[c]));
    },
    makeDock(){
      if(this.isLogin) return null;
      let dock = document.getElementById("ponderDockV2");
      if(!dock){
        dock = document.createElement("div");
        dock.id = "ponderDockV2";
        document.body.appendChild(dock);
      }
      return dock;
    },
    addDockButton(id, label, title, handler){
      if(this.isLogin) return;
      const dock = this.makeDock();
      if(!dock || document.getElementById(id)) return;
      const btn = document.createElement("button");
      btn.id = id;
      btn.className = "ponderDockBtn";
      btn.innerHTML = label;
      btn.title = title;
      btn.onclick = handler;
      dock.appendChild(btn);
    },
    say(message, seconds=7){
      if(this.isLogin) return;
      let b = document.getElementById("ponderSpeechV2");
      if(!b){
        b = document.createElement("div");
        b.id = "ponderSpeechV2";
        document.body.appendChild(b);
      }
      b.innerHTML = "🐕 " + this.esc(message);
      b.style.display = "block";
      clearTimeout(window.__ponderSpeechV2Timer);
      window.__ponderSpeechV2Timer = setTimeout(()=> b.style.display="none", seconds*1000);
    },
    copy(text){
      navigator.clipboard?.writeText(text);
      this.say("Snapshot copied. Send it when you need help debugging.");
    }
  };

  window.PonderV2 = P;
  console.log("🐕 Ponder modular core loaded", P.version);
})();
