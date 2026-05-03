from pathlib import Path

DASH = Path("new_ponder_site/templates/dashboard.html")
SEND = Path("new_ponder_site/templates/send_to_chatgpt.html")
CSS = Path("new_ponder_site/static/style.css")

DASH.with_suffix(".html.backup_snapshot_wire_v1").write_text(DASH.read_text())
CSS.with_suffix(".css.backup_snapshot_wire_v1").write_text(CSS.read_text())

dash = DASH.read_text()

# Upgrade existing AI overview IDs
dash = dash.replace(
    '<div class="ai-score">{{ ai_health }}/100</div>',
    '<div class="ai-score" id="ai-health-score">{{ ai_health }}/100</div>'
)

dash = dash.replace(
    '<div><strong>Capital Engine</strong><span class="sys-good">↑ Online</span><small>{{ capital.get("capital_mode", "UNKNOWN") }}</small></div>',
    '<div><strong>Capital Engine</strong><span class="sys-good" id="capital-status">↑ Online</span><small id="capital-detail">{{ capital.get("capital_mode", "UNKNOWN") }}</small></div>'
)

dash = dash.replace(
    '<div><strong>Decision Engine</strong><span class="sys-good">↑ Active</span><small>{{ decisions.get("summary", {}).get("watch_count", 0) }} watch</small></div>',
    '<div><strong>Decision Engine</strong><span class="sys-good" id="decision-status">↑ Active</span><small id="decision-detail">{{ decisions.get("summary", {}).get("watch_count", 0) }} watch</small></div>'
)

dash = dash.replace(
    '<div><strong>Market Context</strong><span class="sys-warn">→ Cautious</span><small>News {{ news_score }}/100</small></div>',
    '<div><strong>Market Context</strong><span class="sys-warn" id="market-status">→ Cautious</span><small id="market-detail">News {{ news_score }}/100</small></div>'
)

dash = dash.replace(
    '<div><strong>Learning</strong><span class="sys-warn">→ Collecting</span><small>Research-only</small></div>',
    '<div><strong>Learning</strong><span class="sys-warn" id="learning-status">→ Collecting</span><small id="learning-detail">Research-only</small></div>'
)

snapshot_panel = r'''
<section class="card snapshot-panel">
  <div class="money-head">
    <div>
      <div class="eyebrow">Plain-English Snapshot</div>
      <h2>🧠 What Ponder Understands</h2>
      <p class="muted">Live summary from system_snapshot_latest.json.</p>
    </div>
    <button class="copy-btn" onclick="copySystemSnapshot()">Copy Snapshot</button>
  </div>

  <div class="snapshot-grid">
    <div><strong>Top Symbol</strong><span id="top-symbol">—</span></div>
    <div><strong>Top Score</strong><span id="top-score">—</span></div>
    <div><strong>Top Action</strong><span id="top-action">—</span></div>
  </div>

  <div id="ai-plain-feed" class="plain-feed">
    <div>Loading system snapshot...</div>
  </div>
</section>
'''

if "snapshot-panel" not in dash:
    dash = dash.replace('<section class="card brainline">', snapshot_panel + '\n<section class="card brainline">')

snapshot_js = r'''
<script>
function prettyStatus(status) {
  if (status === "online" || status === "active") return "↑ Online";
  if (status === "missing") return "↓ Missing";
  return "→ Unknown";
}

function statusClass(status) {
  if (status === "online" || status === "active") return "sys-good";
  if (status === "missing") return "sys-bad";
  return "sys-warn";
}

async function loadSystemSnapshot() {
  try {
    const res = await fetch("/static/research/system_snapshot_latest.json?t=" + Date.now());
    if (!res.ok) return;
    const data = await res.json();

    const score = document.getElementById("ai-health-score");
    if (score) score.textContent = (data.health_score ?? "—") + "/100";

    const modules = data.modules || {};
    const pairs = [
      ["capital-status", modules.capital_engine, "capital-detail", data.capital?.capital_mode],
      ["decision-status", modules.decision_engine, "decision-detail", (data.decision?.watch_count ?? 0) + " watch"],
      ["market-status", modules.market_intelligence, "market-detail", "Alerts " + (data.risk?.alerts_total ?? 0)],
      ["learning-status", modules.performance_tracker, "learning-detail", "Research-only"]
    ];

    pairs.forEach(([id, st, detailId, detail]) => {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = prettyStatus(st);
        el.className = statusClass(st);
      }
      const detailEl = document.getElementById(detailId);
      if (detailEl) detailEl.textContent = detail || "—";
    });

    const topSymbol = document.getElementById("top-symbol");
    const topScore = document.getElementById("top-score");
    const topAction = document.getElementById("top-action");
    if (topSymbol) topSymbol.textContent = data.decision?.top_symbol || "—";
    if (topScore) topScore.textContent = data.decision?.top_score || "—";
    if (topAction) topAction.textContent = data.decision?.top_action || "—";

    const feed = document.getElementById("ai-plain-feed");
    if (feed) {
      feed.innerHTML = "";
      (data.plain_english || ["No snapshot explanation yet."]).forEach(line => {
        const div = document.createElement("div");
        div.textContent = "• " + line;
        feed.appendChild(div);
      });
    }
  } catch (err) {
    console.log("Snapshot load error", err);
  }
}

async function copySystemSnapshot() {
  try {
    const res = await fetch("/static/research/system_snapshot_latest.json?t=" + Date.now());
    const text = await res.text();
    await navigator.clipboard.writeText(text);
    alert("Snapshot copied — paste it into ChatGPT.");
  } catch (err) {
    alert("Could not copy snapshot.");
  }
}

loadSystemSnapshot();
setInterval(loadSystemSnapshot, 5000);
</script>
'''

if "loadSystemSnapshot" not in dash:
    dash = dash.replace("{% endblock %}", snapshot_js + "\n{% endblock %}")

DASH.write_text(dash)

# Optional: improve Send to ChatGPT page if it exists
if SEND.exists():
    SEND.with_suffix(".html.backup_snapshot_wire_v1").write_text(SEND.read_text())
    SEND.write_text(r'''{% extends "base.html" %}
{% block content %}
<section class="card">
  <div class="eyebrow">Send to ChatGPT</div>
  <h1>📋 Debug Snapshot</h1>
  <p class="muted">Copy this whenever you want help. It prevents guessing and shows the latest system state.</p>
  <button class="copy-btn" onclick="copySnapshot()">Copy Latest Snapshot</button>
  <pre id="snapshotBox" class="snapshot-box">Loading...</pre>
</section>

<script>
async function loadSnapshot() {
  const res = await fetch("/static/research/system_snapshot_latest.json?t=" + Date.now());
  const text = await res.text();
  document.getElementById("snapshotBox").textContent = text;
}
async function copySnapshot() {
  const text = document.getElementById("snapshotBox").textContent;
  await navigator.clipboard.writeText(text);
  alert("Snapshot copied — paste into ChatGPT.");
}
loadSnapshot();
setInterval(loadSnapshot, 5000);
</script>
{% endblock %}
''')

css = CSS.read_text()
if "Snapshot Health Wire v1" not in css:
    css += r'''

/* ===== Snapshot Health Wire v1 ===== */
.snapshot-panel {
  border-color: rgba(167,139,250,.45);
}

.snapshot-grid {
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:12px;
  margin:18px 0;
}

.snapshot-grid div {
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  background:rgba(255,255,255,.025);
}

.snapshot-grid strong {
  display:block;
  color:var(--muted);
  text-transform:uppercase;
  letter-spacing:.08em;
  font-size:12px;
  margin-bottom:8px;
}

.snapshot-grid span {
  display:block;
  font-size:22px;
  font-weight:900;
}

.plain-feed {
  border:1px solid var(--line);
  border-radius:16px;
  padding:16px;
  background:rgba(255,255,255,.025);
  line-height:1.7;
}

.copy-btn {
  border:1px solid rgba(167,139,250,.55);
  background:rgba(167,139,250,.12);
  color:var(--text);
  border-radius:14px;
  padding:10px 14px;
  font-weight:900;
  cursor:pointer;
}

.snapshot-box {
  margin-top:18px;
  white-space:pre-wrap;
  border:1px solid var(--line);
  border-radius:16px;
  padding:16px;
  background:rgba(255,255,255,.025);
  max-height:520px;
  overflow:auto;
}

@media (max-width:800px) {
  .snapshot-grid {
    grid-template-columns:1fr;
  }
}
'''
CSS.write_text(css)

print("✅ Wired snapshot + live module health into dashboard.")
print("✅ Updated Send to ChatGPT page if it exists.")
