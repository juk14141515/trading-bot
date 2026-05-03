from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_overnight_ui_v1").write_text(text)

ADD = r'''

// === PONDER OVERNIGHT INTELLIGENCE UI V1 ===
window.addEventListener("load", function () {
  if (window.__ponderOvernightUIV1) return;
  window.__ponderOvernightUIV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    #ponderOvernightBtn {
      position: fixed;
      right: 22px;
      top: 540px;
      z-index: 100000;
      width: 48px;
      height: 48px;
      border-radius: 16px;
      border: 1px solid rgba(160,190,255,.32);
      background: rgba(8,12,24,.95);
      color: white;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 14px 32px rgba(0,0,0,.38);
    }

    #ponderOvernightPanel {
      display: none;
      position: fixed;
      inset: 58px 34px 34px 260px;
      z-index: 100000;
      overflow: auto;
      padding: 26px;
      border-radius: 26px;
      background:
        radial-gradient(circle at 10% 0%, rgba(120,160,255,.10), transparent 28%),
        radial-gradient(circle at 90% 0%, rgba(124,255,178,.07), transparent 30%),
        rgba(5,8,18,.98);
      border: 1px solid rgba(160,190,255,.20);
      box-shadow: 0 28px 90px rgba(0,0,0,.65);
      color: white;
      font-family: Arial, sans-serif;
    }

    .overnight-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }

    .overnight-card {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,.045);
      border: 1px solid rgba(255,255,255,.08);
    }

    .overnight-card h3 {
      margin: 0 0 8px;
      color: #a8b3c7;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .05em;
    }

    .overnight-big {
      font-size: 25px;
      font-weight: 900;
    }

    .overnight-table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 24px;
      font-size: 13px;
    }

    .overnight-table th,
    .overnight-table td {
      padding: 10px;
      border-bottom: 1px solid rgba(255,255,255,.075);
      text-align: left;
    }

    .overnight-table th {
      color: #a8b3c7;
      font-size: 12px;
      text-transform: uppercase;
    }

    .overnight-close {
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.06);
      color: white;
      cursor: pointer;
      font-weight: 800;
    }

    @media (max-width: 900px) {
      #ponderOvernightPanel { inset: 20px; }
      .overnight-grid { grid-template-columns: 1fr; }
    }
  `;
  document.head.appendChild(style);

  const btn = document.createElement("button");
  btn.id = "ponderOvernightBtn";
  btn.innerHTML = "🌙";
  btn.title = "Overnight Intelligence";
  document.body.appendChild(btn);

  const panel = document.createElement("div");
  panel.id = "ponderOvernightPanel";
  document.body.appendChild(panel);

  function safe(x) {
    if (x === undefined || x === null || Number.isNaN(x)) return "--";
    return x;
  }

  function moveClass(n) {
    const v = Number(n);
    if (v > 0) return "color:#86ff9d";
    if (v < 0) return "color:#ff8b8b";
    return "color:#a8b3c7";
  }

  function row(x) {
    return `
      <tr>
        <td><strong>${safe(x.symbol)}</strong></td>
        <td>${safe(x.price)}</td>
        <td style="${moveClass(x.change_1d_pct)}">${safe(x.change_1d_pct)}%</td>
        <td style="${moveClass(x.change_5d_pct)}">${safe(x.change_5d_pct)}%</td>
        <td>${safe(x.volume_ratio)}x</td>
      </tr>
    `;
  }

  async function loadOvernight() {
    panel.style.display = "block";
    panel.innerHTML = `<h1>🌙 Overnight Intelligence</h1><p style="color:#a8b3c7">Loading overnight brief...</p>`;

    try {
      const res = await fetch("/static/research/overnight_brief_latest.json?ts=" + Date.now());
      const data = await res.json();

      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start">
          <div>
            <h1 style="margin:0;font-size:34px">🌙 Overnight Intelligence</h1>
            <p style="color:#a8b3c7;margin-top:8px">Research-only premarket / overnight awareness layer.</p>
            <p style="color:#7c8aa5;font-size:13px">Updated: ${safe(data.updated_at)}</p>
          </div>
          <button class="overnight-close" id="ponderOvernightClose">Close</button>
        </div>

        <div class="overnight-grid">
          <div class="overnight-card">
            <h3>Market Mode</h3>
            <div class="overnight-big">${safe(data.market_label)}</div>
          </div>
          <div class="overnight-card">
            <h3>Risk Score</h3>
            <div class="overnight-big">${safe(data.risk_score)}/100</div>
          </div>
          <div class="overnight-card">
            <h3>Status</h3>
            <div class="overnight-big">Research Only</div>
          </div>
        </div>

        <h2>Index / Market Tape</h2>
        <table class="overnight-table">
          <thead><tr><th>Symbol</th><th>Price</th><th>1D</th><th>5D</th><th>Volume</th></tr></thead>
          <tbody>${(data.index_moves || []).map(row).join("")}</tbody>
        </table>

        <h2>Top Strength</h2>
        <table class="overnight-table">
          <thead><tr><th>Symbol</th><th>Price</th><th>1D</th><th>5D</th><th>Volume</th></tr></thead>
          <tbody>${(data.top_strength || []).map(row).join("")}</tbody>
        </table>

        <h2>Top Weakness</h2>
        <table class="overnight-table">
          <thead><tr><th>Symbol</th><th>Price</th><th>1D</th><th>5D</th><th>Volume</th></tr></thead>
          <tbody>${(data.top_weakness || []).map(row).join("")}</tbody>
        </table>

        <h2>Brief Notes</h2>
        <div class="overnight-card">
          <ul>${(data.notes || []).map(n => `<li>${n}</li>`).join("")}</ul>
        </div>
      `;

      document.getElementById("ponderOvernightClose").onclick = () => panel.style.display = "none";
    } catch (e) {
      panel.innerHTML = `
        <h1>🌙 Overnight Intelligence</h1>
        <p style="color:#ffb4b4">No overnight brief found.</p>
        <pre>python3 overnight_brief_v1.py</pre>
      `;
    }
  }

  btn.onclick = function () {
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      loadOvernight();
    }
  };
});
'''

if "PONDER OVERNIGHT INTELLIGENCE UI V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Overnight UI installed")
else:
    print("Already installed")
