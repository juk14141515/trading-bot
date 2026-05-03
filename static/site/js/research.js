
async function getJson(path){const r=await fetch(path+'?ts='+Date.now(),{cache:'no-store'});return r.ok?await r.json():{}}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}
function table(rows,keys){return `<table><thead><tr>${keys.map(k=>`<th>${k}</th>`).join('')}</tr></thead><tbody>${(rows||[]).map(r=>`<tr>${keys.map(k=>`<td>${Array.isArray(r[k])?r[k].map(esc).join('<br>'):esc(r[k])}</td>`).join('')}</tr>`).join('')||`<tr><td colspan="${keys.length}">No data</td></tr>`}</tbody></table>`}

async function render(tab='ai'){
 const c=document.getElementById('researchContent');
 if(tab==='ai'){let d=await getJson('/static/research/ai_summary_latest.json');c.innerHTML=`<h2>AI Summary</h2><h3>What Should I Do?</h3><ul>${(d.action_items||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Simple Summary</h3><ul>${(d.plain_english_summary||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`}
 if(tab==='alerts'){let d=await getJson('/static/research/notifications_latest.json');c.innerHTML=`<h2>Alerts</h2>${table(d.alerts||[],['level','category','title','message'])}`}
 if(tab==='market'){let d=await getJson('/static/research/market_intelligence_latest.json');c.innerHTML=`<h2>Market</h2>${table(d.trade_ready||d.top_candidates||[],['symbol','final_score','score','entry_zone','label'])}`}
 if(tab==='overnight'){let d=await getJson('/static/research/overnight_brief_latest.json');c.innerHTML=`<h2>Overnight</h2><p>Market: ${esc(d.market_label)} | Risk: ${esc(d.risk_score)} | News: ${esc(d.news_impact)}</p><ul>${(d.notes||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`}
 if(tab==='sell'){let d=await getJson('/static/research/sell_intelligence_latest.json');c.innerHTML=`<h2>Sell Intelligence</h2>${table(d.sell_candidates||[],['symbol','sell_pressure','verdict','reasons'])}`}
 if(tab==='rotation'){let d=await getJson('/static/research/rotation_engine_latest.json');c.innerHTML=`<h2>Rotation</h2>${table(d.rotation_suggestions||[],['sell_symbol','buy_symbol','action','rotation_score','confidence','regime'])}`}
 if(tab==='performance'){let d=await getJson('/static/research/rotation_performance_latest.json');c.innerHTML=`<h2>Performance</h2><pre>${esc(JSON.stringify(d.summary||d,null,2))}</pre>`}
 if(tab==='debug'){c.innerHTML=`<h2>Debug</h2><button onclick="copyDebug()">Copy Debug Snapshot</button>`}
}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>render(b.dataset.tab));
render('ai');
