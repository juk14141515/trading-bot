from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot/new_ponder_site")
T = ROOT / "templates"
S = ROOT / "static"

# Better dashboard
(T / "dashboard.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Ponder Invest AI</h1>
<p class="muted">Research-only capital intelligence system. No live orders.</p>

{% set read = ai.get("key_readout", {}) %}
{% set alerts_sum = alerts.get("summary", {}) %}

<section class="hero">
  <div>
    <h2>Today’s Command</h2>
    <p>Stay disciplined. Let the system learn before automation.</p>
  </div>
  <div class="pill">Research Mode</div>
</section>

<section class="grid">
  <div class="card"><h3>Market Regime</h3><div class="big">{{ read.get("regime", "—") }}</div><p>Score: {{ read.get("regime_score", "—") }}</p></div>
  <div class="card"><h3>News Impact</h3><div class="big">{{ read.get("news_impact", "—") }}</div><p>Higher = more defensive</p></div>
  <div class="card"><h3>Top Rotation</h3><div class="big">{{ read.get("top_rotation", {}).get("move", "—") }}</div><p>{{ read.get("top_rotation", {}).get("action", "") }}</p></div>
  <div class="card"><h3>System Alerts</h3><div class="big">{{ alerts_sum.get("total", 0) }}</div><p>{{ alerts_sum.get("critical", 0) }} critical · {{ alerts_sum.get("warning", 0) }} warnings</p></div>
</section>

<section class="grid">
  <div class="card">
    <h3>Adaptive Capital AI</h3>
    <div class="big">Next</div>
    <p>Build allocation recommendations based on confidence, unused capital, and rotation results.</p>
  </div>
  <div class="card">
    <h3>Shadow Execution</h3>
    <div class="big">Safe</div>
    <p>Simulate sell/buy actions before connecting anything live.</p>
  </div>
  <div class="card">
    <h3>Daily Discipline</h3>
    <div class="big">Guarded</div>
    <p>No live automation until the tracker proves edge.</p>
  </div>
</section>

<section class="card highlight">
  <h2>What Should I Do?</h2>
  <ul>
    {% for item in ai.get("action_items", []) %}
      <li>{{ item }}</li>
    {% else %}
      <li>Review AI Summary, Alerts, and Rotation before changing anything.</li>
    {% endfor %}
  </ul>
</section>

<section class="card">
  <h2>Plain-English Summary</h2>
  <ul>
    {% for item in ai.get("plain_english_summary", []) %}
      <li>{{ item }}</li>
    {% else %}
      <li>No summary yet.</li>
    {% endfor %}
  </ul>
</section>
{% endblock %}
''')

# Better assistant
(T / "assistant.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>🐕 Ask Ponder</h1>
<p class="muted">Ponder is your research-only trading assistant and system overseer.</p>

<section class="grid">
  <div class="card"><h3>Mode</h3><div class="big">{{ ai.get("key_readout", {}).get("regime", "—") }}</div><p>Ponder watches risk first.</p></div>
  <div class="card"><h3>News Impact</h3><div class="big">{{ ai.get("key_readout", {}).get("news_impact", "—") }}</div><p>High news = fewer forced trades.</p></div>
  <div class="card"><h3>Learning</h3><div class="big">{{ ai.get("key_readout", {}).get("pending_evaluations", "—") }}</div><p>Pending outcomes.</p></div>
</section>

<section class="card">
  <h2>Quick Questions</h2>
  <button onclick="answer('why_no_trade')">Why didn’t you trade?</button>
  <button onclick="answer('what_to_do')">What should I do now?</button>
  <button onclick="answer('biggest_risk')">Biggest risk?</button>
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

# Better learning
(T / "learning.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Learning Center</h1>
<p class="muted">Game layer for discipline, progress, and safer improvement.</p>

{% set pending = performance.get("summary", {}).get("pending_evaluations", 0) %}
{% set evaluated = performance.get("summary", {}).get("evaluated", 0) %}
{% set unlocked = achievements.get("total_unlocked", achievements.get("achievements", [])|length) %}

<section class="grid">
  <div class="card"><h3>XP</h3><div class="big">{{ unlocked * 25 + evaluated * 5 }}</div><p>Research learning points</p></div>
  <div class="card"><h3>Achievements</h3><div class="big">{{ unlocked }}</div><p>Unlocked</p></div>
  <div class="card"><h3>Pending Evaluations</h3><div class="big">{{ pending }}</div><p>Let the tracker collect outcomes.</p></div>
  <div class="card"><h3>Automation Readiness</h3><div class="big">Not Yet</div><p>Need stable edge first.</p></div>
</section>

<section class="card highlight">
  <h2>Daily Missions</h2>
  <ul>
    <li>Review AI Summary.</li>
    <li>Check Alerts before trusting any signal.</li>
    <li>Let rotation tracker collect more outcomes.</li>
    <li>Keep new modules research-only.</li>
    <li>Copy Debug Snapshot before asking for help.</li>
  </ul>
</section>

<section class="card">
  <h2>Future Unlocks</h2>
  <ul>
    <li>Adaptive Capital Allocator v1</li>
    <li>Unused Capital Optimizer</li>
    <li>Sell Intelligence v2</li>
    <li>Shadow Execution Tracker</li>
    <li>IPO / Day Trading / Crypto Research Labs</li>
  </ul>
</section>
{% endblock %}
''')

# Better CSS
css = (S / "style.css").read_text()
css += r'''

/* sleep_v1 polish */
.hero{
  border:1px solid var(--border);
  border-radius:24px;
  padding:24px;
  margin:24px 0;
  background:
    radial-gradient(circle at top right, rgba(147,197,253,.16), transparent 35%),
    linear-gradient(180deg,var(--card),var(--panel));
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:20px;
}
.hero h2{font-size:30px;margin:0 0 6px}
.pill{
  border:1px solid var(--accent);
  border-radius:999px;
  padding:10px 14px;
  font-weight:900;
  color:var(--accent);
  white-space:nowrap;
}
.highlight{
  border-color:rgba(147,197,253,.55);
  box-shadow:0 0 0 1px rgba(147,197,253,.08), 0 20px 60px rgba(0,0,0,.25);
}
.card h3{
  color:#bfdbfe;
  margin-top:0;
}
.card p{
  color:var(--muted);
}
li{
  margin:7px 0;
  line-height:1.45;
}
.side{
  box-shadow:12px 0 40px rgba(0,0,0,.22);
}
.main{
  padding-bottom:80px;
}
'''
(S / "style.css").write_text(css)

print("✅ Sleep v1 polish installed")
print("Restart the new site if it is running.")
