from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_sell_intel_ui_v1").write_text(text)

ADD = r'''

// === PONDER SELL INTELLIGENCE UI V1 ===
window.addEventListener("load", function () {
  if (window.__ponderSellIntelUIV1) return;
  window.__ponderSellIntelUIV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    #ponderSellIntelBtn {
      position: fixed;
      right: 22px;
      top: 600px;
      z-index: 100000;
      width: 48px;
      height: 48px;
      border-radius: 16px;
      border: 1px solid rgba(255,170,120,.32);
      background: rgba(8,12,24,.95);
      color: white;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 14px 32px rgba(0,0,0,.38);
    }

    #ponderSellIntelPanel {
      display: none;
      position: fixed;
      inset: 58px 34px 34px 260px;
      z-index: 100000;
      overflow: auto;
      padding: 26px;
      border-radius: 26px;
      background:
        radial-gradient(circle at 10% 0%, rgba(255,120,120,.10), transparent 28%),
        radial-gradient(circle at 90% 0%, rgba(124,255,178,.06), transparent 30%),
        rgba(5,8,18,.98);
      border: 1px solid rgba(255,170,120,.20);
      box-shadow: 0 28px 90px rgba(0,0,0,.65);
      color: white;
      font-family: Arial, sans-serif;
    }

    .sell-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }

    .sell-card {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,.045);
      border: 1px solid rgba(255,255,255,.08);
    }

    .sell-card h3 {
      margin: 0 0 8px;
      color: #a8b3c7;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .05em;
    }

    .sell-big {
      font-size: 25px;
      font-weight: 900;
    }

    .sell-table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 24px;
      font-size: 13px;
    }

    .sell-table th,
    .sell-table td {
      padding: 10px;
      border-bottom: 1px solid rgba(255,255,255,.075);
      text-align: left;
      vertical-align: top;
    }

    .sell-table th {
      color: #a8b3c7;
      font-size: 12px;
      text-transform: uppercase;
    }

    .sell-close {
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.06);
      color: white;
      cursor: pointer;
      font-weight: 800;
    }

    @media (max-width: 900px) {
      #ponderSellIntelPanel { inset: 20px; }
      .sell-grid { grid-template-columns: 1fr; }
    }
  `;
  document.head.appendChild(style);

  const btn = document.createElement("button");
  btn.id = "ponderSellIntelBtn";
  btn.innerHTML = "🛡️";
  btn.title = "Sell Intelligence";
  document.body.appendChild(btn);

  const panel = document.createElement("div");
  panel.id = "ponderSellIntelPanel";
  document.body.appendChild(panel);

  function safe(x) {
    if (x === undefined || x === null || Number.isNaN(x)) return "--";
    return x;
  }

  function pressureColor(x) {
    const n = Number(x);
    if (n >= 75) return "color:#ff8b8b";
    if (n >= 50) return "color:#ffd36d";
    if (n >= 30) return "color:#fff18a";
    return "color:#86ff9d";
  }

  function row(x) {
    return `
      <tr>
        <td><strong>${safe(x.symbol)}</strong></td>
        <td style="${pressureColor(x.sell_pressure)};font-weight:900">${safe(x.sell_pressure)}/100</td>
        <td>${safe(x.verdict)}</td>
        <td>${safe(x.change_30m_pct)}%</td>
        <td>${safe(x.change_60m_pct)}%</td>
        <td>${safe(x.pullback_from_high_pct)}%</td>
        <td>${safe(x.volume_ratio)}x</td>
        <td>${(x.reasons || []).join("<br>")}</td>
      </tr>
    `;
  }

  async function loadSellIntel() {
    panel.style.display = "block";
    panel.innerHTML = `<h1>🛡️ Sell Intelligence</h1><p style="color:#a8b3c7">Loading sell pressure research...</p>`;

    try {
      const res = await fetch("/static/research/sell_intelligence_latest.json?ts=" + Date.now());
      const data = await res.json();
      const top = data.top_exit_candidate || {};
      const candidates = data.sell_candidates || [];

      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start">
          <div>
            <h1 style="margin:0;font-size:34px">🛡️ Sell Intelligence</h1>
            <p style="color:#a8b3c7;margin-top:8px">Research-only exit pressure layer. Does not place sell orders.</p>
            <p style="color:#7c8aa5;font-size:13px">Updated: ${safe(data.updated_at)}</p>
          </div>
          <button class="sell-close" id="ponderSellIntelClose">Close</button>
        </div>

        <div class="sell-grid">
          <div class="sell-card">
            <h3>Top Exit Candidate</h3>
            <div class="sell-big">${safe(top.symbol)}</div>
            <div style="color:#a8b3c7;font-size:13px">${safe(top.verdict)}</div>
          </div>
          <div class="sell-card">
            <h3>Sell Pressure</h3>
            <div class="sell-big" style="${pressureColor(top.sell_pressure)}">${safe(top.sell_pressure)}/100</div>
            <div style="color:#a8b3c7;font-size:13px">Higher = more exit risk</div>
          </div>
          <div class="sell-card">
            <h3>Status</h3>
            <div class="sell-big">Research Only</div>
            <div style="color:#a8b3c7;font-size:13px">No live sell control</div>
          </div>
        </div>

        <h2>Exit Pressure Ranking</h2>
        <table class="sell-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Pressure</th>
              <th>Verdict</th>
              <th>30m</th>
              <th>60m</th>
              <th>From High</th>
              <th>Vol</th>
              <th>Reasons</th>
            </tr>
          </thead>
          <tbody>${candidates.map(row).join("")}</tbody>
        </table>

        <h2>Notes</h2>
        <div class="sell-card">
          <ul>${(data.notes || []).map(n => `<li>${n}</li>`).join("")}</ul>
        </div>
      `;

      document.getElementById("ponderSellIntelClose").onclick = () => panel.style.display = "none";
    } catch (e) {
      panel.innerHTML = `
        <h1>🛡️ Sell Intelligence</h1>
        <p style="color:#ffb4b4">No sell intelligence file found.</p>
        <pre>python3 sell_intelligence_v1.py</pre>
      `;
    }
  }

  btn.onclick = function () {
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      loadSellIntel();
    }
  };
});
'''

if "PONDER SELL INTELLIGENCE UI V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Sell Intelligence UI installed")
else:
    print("Already installed")
