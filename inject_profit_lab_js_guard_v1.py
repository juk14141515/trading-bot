from pathlib import Path
from datetime import datetime
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_lab_js_guard_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

old = '''  document.getElementById("todayPnl").textContent=money(lab.net_today);
  document.getElementById("todayPnl").className="value "+cls(lab.net_today);
  document.getElementById("todayStats").textContent=`${lab.buys_today||0} buys · ${lab.sells_today||0} sells`;
  document.getElementById("todayWin").textContent=pct(lab.win_rate_today);
  document.getElementById("todayWL").textContent=`${lab.wins_today||0} wins · ${lab.losses_today||0} losses`;
  document.getElementById("health").textContent=(h.score??"--")+"/100";
  document.getElementById("healthNote").textContent=h.note||"";
  document.getElementById("openPl").textContent=money(l.open_pl);
  document.getElementById("openPl").className="value "+cls(l.open_pl);

  let counts=logs.counts||{};
  document.getElementById("events").innerHTML="<tbody>"+Object.keys(counts).map(k=>`<tr><th>${k}</th><td>${counts[k]}</td></tr>`).join("")+"</tbody>";'''

new = '''  let el;
  el=document.getElementById("todayPnl"); if(el){el.textContent=money(lab.net_today); el.className="value "+cls(lab.net_today);}
  el=document.getElementById("todayStats"); if(el){el.textContent=`${lab.buys_today||0} buys · ${lab.sells_today||0} sells`;}
  el=document.getElementById("todayWin"); if(el){el.textContent=pct(lab.win_rate_today);}
  el=document.getElementById("todayWL"); if(el){el.textContent=`${lab.wins_today||0} wins · ${lab.losses_today||0} losses`;}
  el=document.getElementById("health"); if(el){el.textContent=(h.score??"--")+"/100";}
  el=document.getElementById("healthNote"); if(el){el.textContent=h.note||"";}
  el=document.getElementById("openPl"); if(el){el.textContent=money(l.open_pl); el.className="value "+cls(l.open_pl);}

  let counts=logs.counts||{};
  el=document.getElementById("events");
  if(el){
    el.innerHTML="<tbody>"+Object.keys(counts).map(k=>`<tr><th>${k}</th><td>${counts[k]}</td></tr>`).join("")+"</tbody>";
  }'''

if old in txt:
    txt = txt.replace(old, new)
else:
    print("WARNING: exact block not found. Applying smaller safety patch.")
    txt = txt.replace('document.getElementById("todayPnl").textContent=money(lab.net_today);', 'let el; el=document.getElementById("todayPnl"); if(el){el.textContent=money(lab.net_today);}')
    txt = txt.replace('document.getElementById("todayPnl").className="value "+cls(lab.net_today);', 'el=document.getElementById("todayPnl"); if(el){el.className="value "+cls(lab.net_today);}')
    txt = txt.replace('document.getElementById("todayStats").textContent=`${lab.buys_today||0} buys · ${lab.sells_today||0} sells`;', 'el=document.getElementById("todayStats"); if(el){el.textContent=`${lab.buys_today||0} buys · ${lab.sells_today||0} sells`;}' )
    txt = txt.replace('document.getElementById("todayWin").textContent=pct(lab.win_rate_today);', 'el=document.getElementById("todayWin"); if(el){el.textContent=pct(lab.win_rate_today);}')
    txt = txt.replace('document.getElementById("todayWL").textContent=`${lab.wins_today||0} wins · ${lab.losses_today||0} losses`;', 'el=document.getElementById("todayWL"); if(el){el.textContent=`${lab.wins_today||0} wins · ${lab.losses_today||0} losses`;}' )
    txt = txt.replace('document.getElementById("health").textContent=(h.score??"--")+"/100";', 'el=document.getElementById("health"); if(el){el.textContent=(h.score??"--")+"/100";}')
    txt = txt.replace('document.getElementById("healthNote").textContent=h.note||"";', 'el=document.getElementById("healthNote"); if(el){el.textContent=h.note||"";}')
    txt = txt.replace('document.getElementById("openPl").textContent=money(l.open_pl);', 'el=document.getElementById("openPl"); if(el){el.textContent=money(l.open_pl);}')
    txt = txt.replace('document.getElementById("openPl").className="value "+cls(l.open_pl);', 'el=document.getElementById("openPl"); if(el){el.className="value "+cls(l.open_pl);}')

# Also guard chart canvas
txt = txt.replace(
    'if(!chart){chart=new Chart(document.getElementById("chart"),{type:"line",data:{labels:labels,datasets:data},options:opts})}',
    'let chartEl=document.getElementById("chart"); if(chartEl && !chart){chart=new Chart(chartEl,{type:"line",data:{labels:labels,datasets:data},options:opts})}'
)

# Guard replay if the previous patch left it unguarded
txt = txt.replace(
    'document.getElementById("replay").innerHTML=(d.recent_trades||[]).map(t=>',
    'if(document.getElementById("replay")){document.getElementById("replay").innerHTML=(d.recent_trades||[]).map(t=>'
)

txt = txt.replace(
    '|| "<tr><td colspan=\'9\'>No replay rows yet.</td></tr>";\n  if(document.getElementById("positionRows")){',
    '|| "<tr><td colspan=\'9\'>No replay rows yet.</td></tr>";}\n  if(document.getElementById("positionRows")){'
)

p.write_text(txt)
print("DONE: Profit Lab JS guard installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
