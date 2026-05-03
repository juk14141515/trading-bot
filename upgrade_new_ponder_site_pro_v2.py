from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot/new_ponder_site")
T = ROOT / "templates"
S = ROOT / "static"

(T / "dashboard.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<section class="hero pro-hero">
  <div>
    <div class="eyebrow">Research Mode · No Live Orders</div>
    <h1>Ponder Invest AI</h1>
    <p class="muted">A clean command center for market intelligence, capital discipline, learning, and future automation.</p>
  </div>
  <div class="hero-dog">
    <div class="dog-icon">🐕</div>
    <div>
      <strong>Ponder is watching.</strong>
      <p class="muted">Risk first. Patience over forced trades.</p>
    </div>
  </div>
</section>

{% set read = ai.get("key_readout", {}) %}
{% set alerts_sum = alerts.get("summary", {}) %}

<section class="grid">
  <div class="card metric"><h3>Market Regime</h3><div class="big">{{ read.get("regime", "—") }}</div><p>Score: {{ read.get("regime_score", "—") }}</p></div>
  <div class="card metric"><h3>News Impact</h3><div class="big">{{ read.get("news_impact", "—") }}</div><p>Higher = more defensive</p></div>
  <div class="card metric"><h3>Top Rotation</h3><div class="big small-big">{{ read.get("top_rotation", {}).get("move", "—") }}</div><p>{{ read.get("top_rotation", {}).get("action", "") }}</p></div>
  <div class="card metric"><h3>Alerts</h3><div class="big">{{ alerts_sum.get("total", 0) }}</div><p>{{ alerts_sum.get("critical", 0) }} critical · {{ alerts_sum.get("warning", 0) }} warnings</p></div>
</section>

<section class="split">
  <div class="card highlight">
    <h2>🧭 What Should I Do?</h2>
    <ul>
      {% for item in ai.get("action_items", []) %}
        <li>{{ item }}</li>
      {% else %}
        <li>Review AI Summary, Alerts, and Rotation before changing anything.</li>
      {% endfor %}
    </ul>
  </div>

  <div class="card">
    <h2>🚦 Automation Readiness</h2>
    <div class="readiness">
      <div><span class="dot warn"></span> Research-only mode</div>
      <div><span class="dot warn"></span> Waiting for more evaluated outcomes</div>
      <div><span class="dot good"></span> Data collection active</div>
      <div><span class="dot risk"></span> Live automation disabled</div>
    </div>
  </div>
</section>

<section class="card">
  <h2>Plain-English Summary</h2>
  <ul class="summary-list">
    {% for item in ai.get("plain_english_summary", []) %}
      <li>{{ item }}</li>
    {% else %}
      <li>No summary yet.</li>
    {% endfor %}
  </ul>
</section>

<section class="grid">
  <a class="card module-link" href="/research">
    <h3>🧠 Research Center</h3>
    <p>AI summary, alerts, scanner, overnight, sell, rotation, and performance.</p>
  </a>
  <a class="card module-link" href="/assistant">
    <h3>🐕 Ask Ponder</h3>
    <p>Ask why no trade, where risk is, and what to focus on next.</p>
  </a>
  <a class="card module-link" href="/learning">
    <h3>🎮 Learning Center</h3>
    <p>Achievements, daily missions, XP, and progress toward safe automation.</p>
  </a>
  <a class="card module-link" href="/settings">
    <h3>⚙️ Settings</h3>
    <p>Theme and debug tools. More customization coming next.</p>
  </a>
</section>

<section class="card roadmap">
  <h2>Next Build Targets</h2>
  <div class="roadmap-grid">
    <div><strong>1. Adaptive Capital Allocator</strong><p>Recommend position sizing from confidence, utilization, and rotation history.</p></div>
    <div><strong>2. Unused Capital Optimizer</strong><p>Detect cash sitting idle when high-quality setups exist.</p></div>
    <div><strong>3. Shadow Execution</strong><p>Simulate sell/buy decisions before real automation.</p></div>
    <div><strong>4. Sell Intelligence v2</strong><p>Compare hold vs sell expected value with trailing stop simulation.</p></div>
  </div>
</section>
{% endblock %}
''')

(T / "research.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Research Center</h1>
<p class="muted">All non-live intelligence modules in one organized view.</p>

<div class="tabs">
  <button onclick="showTab('ai')">AI Summary</button>
  <button onclick="showTab('alerts')">Alerts</button>
  <button onclick="showTab('market')">Market</button>
  <button onclick="showTab('overnight')">Overnight</button>
  <button onclick="showTab('sell')">Sell</button>
  <button onclick="showTab('rotation')">Rotation</button>
  <button onclick="showTab('performance')">Performance</button>
  <button onclick="showTab('shadow')">Shadow</button>
  <button onclick="showTab('future')">Future Labs</button>
</div>

<section id="tab-ai" class="tab card">
  <h2>🤖 AI Summary</h2>
  {% set ai = data.get("ai", {}) %}
  <h3>What Should I Do?</h3>
  <ul>{% for x in ai.get("action_items", []) %}<li>{{ x }}</li>{% else %}<li>No action items yet.</li>{% endfor %}</ul>
  <h3>Simple Summary</h3>
  <ul>{% for x in ai.get("plain_english_summary", []) %}<li>{{ x }}</li>{% else %}<li>No summary yet.</li>{% endfor %}</ul>
</section>

<section id="tab-alerts" class="tab card" style="display:none">
  <h2>🔔 Alerts</h2>
  {% set alerts = data.get("alerts", {}) %}
  <table>
    <thead><tr><th>Level</th><th>Category</th><th>Title</th><th>Message</th></tr></thead>
    <tbody>
      {% for a in alerts.get("alerts", []) %}
        <tr><td>{{ a.get("level") }}</td><td>{{ a.get("category") }}</td><td><strong>{{ a.get("title") }}</strong></td><td>{{ a.get("message") }}</td></tr>
      {% else %}
        <tr><td colspan="4">No alerts.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</section>

{% for name in ["market","overnight","sell","rotation","performance","shadow"] %}
<section id="tab-{{ name }}" class="tab card" style="display:none">
  <h2>{{ name|title }}</h2>
  <pre>{{ data.get(name, {}) | tojson(indent=2) }}</pre>
</section>
{% endfor %}

<section id="tab-future" class="tab card" style="display:none">
  <h2>Future Research Labs</h2>
  <div class="grid">
    <div class="card mini"><h3>IPO Watch</h3><p>Track upcoming IPOs, hype, lockups, and early price behavior.</p></div>
    <div class="card mini"><h3>Day Trading Lab</h3><p>Fast-market setups with different entries/exits, research-only.</p></div>
    <div class="card mini"><h3>Crypto / ETF / Commodities</h3><p>Separate market scanners and learning outputs later.</p></div>
    <div class="card mini"><h3>Social Trend Scanner</h3><p>TikTok/social catalyst research, not live trading.</p></div>
    <div class="card mini"><h3>Event Impact Layer</h3><p>News/event tagging and historical outcome learning.</p></div>
    <div class="card mini"><h3>Strategy Sandbox</h3><p>Paper-test parameter changes before applying anything.</p></div>
  </div>
</section>

<script>
function showTab(name){
  document.querySelectorAll('.tab').forEach(x => x.style.display='none');
  document.getElementById('tab-'+name).style.display='block';
}
</script>
{% endblock %}
''')

(T / "assistant.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>🐕 Ask Ponder</h1>
<p class="muted">Ponder is your research-only assistant and system overseer.</p>

<section class="hero assistant-hero">
  <div class="dog-icon">🐕</div>
  <div>
    <h2>Ponder’s Job</h2>
    <p>Explain the system, warn you when risk is high, and help you avoid emotional trades.</p>
  </div>
</section>

<section class="grid">
  <div class="card"><h3>Mode</h3><div class="big">{{ ai.get("key_readout", {}).get("regime", "—") }}</div><p>Risk-first assistant</p></div>
  <div class="card"><h3>News Impact</h3><div class="big">{{ ai.get("key_readout", {}).get("news_impact", "—") }}</div><p>High news = caution</p></div>
  <div class="card"><h3>Learning</h3><div class="big">{{ ai.get("key_readout", {}).get("pending_evaluations", "—") }}</div><p>Pending outcomes</p></div>
</section>

<section class="card">
  <h2>Quick Questions</h2>
  <button onclick="answer('why_no_trade')">Why didn’t you trade?</button>
  <button onclick="answer('what_to_do')">What should I do now?</button>
  <button onclick="answer('biggest_risk')">Biggest risk?</button>
  <button onclick="answer('should_rotate')">Should I rotate?</button>
  <button onclick="answer('plain_english')">Explain simply</button>
</section>

<section class="card highlight" id="answer">Click a question and Ponder will answer from current research data.</section>

<script>
const answers = {{ assistant.get("answers", {}) | tojson }};
const fallback = {{ ai.get("action_items", []) | tojson }};
function answer(key){
  const items = answers[key] || fallback || ["No answer yet."];
  document.getElementById("answer").innerHTML = "<ul>" + items.map(x => `<li>${x}</li>`).join("") + "</ul>";
}
</script>
{% endblock %}
''')

(T / "settings.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Settings</h1>
<p class="muted">Simple controls now. Full config editing can come later.</p>

<section class="card">
  <h2>Theme</h2>
  <button onclick="setTheme('blue')">Blue</button>
  <button onclick="setTheme('slate')">Slate</button>
  <button onclick="setTheme('purple')">Purple</button>
</section>

<section class="card">
  <h2>Tools</h2>
  <button onclick="copyDebug()">Copy Debug Snapshot</button>
  <button onclick="localStorage.clear(); alert('Local settings cleared')">Reset Local Settings</button>
</section>

<script>
function setTheme(name){
  localStorage.setItem('ponderTheme', name);
  document.body.className = 'theme-' + name;
}
function copyDebug(){
  navigator.clipboard.writeText(JSON.stringify({
    time:new Date().toISOString(),
    page:location.href,
    note:"new_ponder_site debug snapshot"
  }, null, 2));
  alert("Debug snapshot copied");
}
</script>
{% endblock %}
''')

css = (S / "style.css").read_text()
css += r'''

/* pro_v2 */
body.theme-blue{--accent:#93c5fd}
body.theme-slate{--accent:#cbd5e1}
body.theme-purple{--accent:#c4b5fd}

.pro-hero{
  min-height:180px;
}
.eyebrow{
  color:var(--accent);
  font-weight:900;
  letter-spacing:.08em;
  text-transform:uppercase;
  font-size:12px;
  margin-bottom:8px;
}
.hero-dog,.assistant-hero{
  display:flex;
  gap:14px;
  align-items:center;
}
.dog-icon{
  width:76px;
  height:76px;
  border-radius:26px;
  border:1px solid var(--accent);
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:34px;
  background:rgba(147,197,253,.08);
}
.metric{
  min-height:150px;
}
.small-big{
  font-size:22px;
}
.split{
  display:grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, .9fr);
  gap:16px;
}
.readiness div{
  margin:10px 0;
  color:var(--muted);
}
.dot{
  display:inline-block;
  width:10px;
  height:10px;
  border-radius:999px;
  margin-right:8px;
}
.dot.good{background:var(--good)}
.dot.warn{background:var(--warn)}
.dot.risk{background:var(--risk)}
.summary-list li{
  padding:7px 0;
}
.module-link{
  text-decoration:none;
  color:var(--text);
  display:block;
  transition:transform .15s ease,border-color .15s ease;
}
.module-link:hover{
  transform:translateY(-2px);
  border-color:var(--accent);
}
.roadmap-grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:14px;
}
.roadmap-grid div{
  border:1px solid var(--border);
  border-radius:16px;
  padding:14px;
  background:#07111f;
}
.mini{
  margin:0;
}
@media(max-width:950px){
  .split{grid-template-columns:1fr}
}
'''
(S / "style.css").write_text(css)

print("✅ Pro v2 site upgrade installed")
