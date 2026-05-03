
async function getJson(path){const r=await fetch(path+'?ts='+Date.now(),{cache:'no-store'});return r.ok?await r.json():{}}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}
function card(t,v,n=''){return `<div class="card"><h3>${t}</h3><div class="big">${v??'—'}</div><p class="muted">${n}</p></div>`}

async function loadOverview(){
  const ai=await getJson('/static/research/ai_summary_latest.json');
  const alerts=await getJson('/static/research/notifications_latest.json');
  const read=ai.key_readout||{};
  const el=document.getElementById('overviewCards');
  if(el) el.innerHTML=[
    card('Regime', read.regime, 'Market mode'),
    card('News Impact', read.news_impact, 'Higher means more caution'),
    card('Top Rotation', (read.top_rotation||{}).move, (read.top_rotation||{}).action||''),
    card('Alerts', (alerts.summary||{}).total||0, `${(alerts.summary||{}).critical||0} critical`)
  ].join('');
  const actions=document.getElementById('actionItems');
  if(actions) actions.innerHTML=(ai.action_items||[]).map(x=>`<li>${esc(x)}</li>`).join('');
}

async function openPonder(){
  const p=document.getElementById('ponderPanel');
  const ai=await getJson('/static/research/ai_summary_latest.json');
  const assistant=await getJson('/static/research/ponder_assistant_latest.json');
  p.style.display=p.style.display==='block'?'none':'block';
  p.innerHTML=`<h2>🐕 Ask Ponder</h2>
    <button data-q="why_no_trade">Why didn’t you trade?</button>
    <button data-q="what_to_do">What should I do?</button>
    <button data-q="biggest_risk">Biggest risk?</button>
    <div id="ponderAnswer" class="card">Click a question.</div>`;
  p.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>{
    const items=(assistant.answers||{})[b.dataset.q] || ai.action_items || ['No answer yet.'];
    document.getElementById('ponderAnswer').innerHTML='<ul>'+items.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>';
  });
}
document.getElementById('ponderAssistantBtn')?.addEventListener('click',openPonder);
loadOverview();
setInterval(loadOverview,45000);

function copyDebug(){
  Promise.all([
    getJson('/static/research/ai_summary_latest.json'),
    getJson('/static/research/notifications_latest.json'),
    getJson('/static/research/rotation_engine_latest.json')
  ]).then(([ai,alerts,rotation])=>{
    navigator.clipboard.writeText(JSON.stringify({time:new Date().toISOString(),url:location.href,ai:ai.key_readout,alerts:alerts.summary,rotation:rotation.top_rotation},null,2));
    alert('Debug snapshot copied');
  });
}
