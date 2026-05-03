from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_intelligence_ui_v2").write_text(text)

ADD = r'''

// === PONDER INTELLIGENCE UI V2 ===
window.addEventListener("load", function () {
  if (window.__ponderIntelUIV2) return;
  window.__ponderIntelUIV2 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    #ponderIntelBtn {
      position: fixed;
      right: 22px;
      top: 420px;
      z-index: 100000;
      width: 48px;
      height: 48px;
      border-radius: 16px;
      border: 1px solid rgba(120,180,255,.35);
      background: rgba(10,14,28,.94);
      color: white;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 12px 30px rgba(0,0,0,.35);
    }

    #ponderIntelPanel {
      display: none;
      position: fixed;
      inset: 60px 34px 34px 260px;
      z-index: 100000;
      overflow: auto;
      padding: 26px;
      border-radius: 26px;
      background:
        radial-gradient(circle at 20% 0%, rgba(110,255,170,.08), transparent 30%),
        linear-gradient(180deg, rgba(9,13,25,.98), rgba(4,6,12,.98));
      color: white;
      border: 1px solid rgba(140,160,255,.22);
      box-shadow: 0 26px 80px rgba(0,0,0,.62);
      font-family: Arial, sans-serif;
    }

    .intel-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin: 18px 0 24px;
    }

    .intel-card {
      padding: 18px;
      border-radius: 20px;
      border: 1px solid rgba(255,255,255,.08);
      background: rgba(255,255,255,.045);
    }

    .intel-card h3 {
      margin: 0 0 8px;
      font-size: 14px;
      color: #a8b3c7;
    }

    .intel-card .big {
      font-size: 26px;
      font-weight: 900;
    }

    .intel-table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 28px;
      font-size: 13px;
    }

    .intel-table th, .intel-table td {
      padding: 10px;
      border-bottom: 1px solid rgba(255,255,255,.075);
      text-align: left;
    }

    .intel-table th {
      color: #a8b3c7;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }

    .intel-badge {
      display: inline-block;
      padding: 5px 9px;
      border-radius: 999px;
      background: rgba(255,255,255,.07);
      border: 1px solid rgba(255,255,255,.08);
      white-space: nowrap;
    }

    .intel-close {
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.06);
      color: white;
      cursor: pointer;
      font-weight: 800;
    }

    @media (max-width: 900px) {
      #ponderIntelPanel {
        inset: 20px;
      }
      .intel-grid {
        grid-template-columns: 1fr;
      }
    }
  `;
  document.head.appendChild(style);

  const btn = document.createElement("button");
  btn.id = "ponderIntelBtn";
  btn.innerHTML = "🧠";
  btn.title = "Market Intelligence";
  document.body.appendChild(btn);

  const panel = document.createElement("div");
  panel.id = "ponderIntelPanel";
  document.body.appendChild(panel);

  function safe(n) {
    if (n === undefined || n === null || Number.isNaN(n)) return "--";
    return n;
  }

  function row(x) {
    return `
      <tr>
        <td><strong>${safe(x.symbol)}</strong></td>
        <td>${safe(x.final_score)}</td>
        <td><span class="intel-badge">${safe(x.entry_zone)}</span></td>
        <td>${safe(x.pullback_from_sma5_pct)}%</td>
        <td>${safe(x.extension_from_sma20_pct)}%</td>
        <td>${safe(x.change_5d_pct)}%</td>
        <td>${safe(x.volume_ratio)}x</td>
        <td>${safe(x.label)}</td>
      </tr>
    `;
  }

  function table(title, items) {
    return `
      <h2>${title}</h2>
      <table class="intel-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Score</th>
            <th>Entry Zone</th>
            <th>Pullback</th>
            <th>Extension</th>
            <th>5D</th>
            <th>Vol</th>
            <th>Label</th>
          </tr>
        </thead>
        <tbody>${(items || []).map(row).join("")}</tbody>
      </table>
    `;
  }

  async function loadIntel() {
    panel.style.display = "block";
    panel.innerHTML = `<h1>🧠 Market Intelligence</h1><p style="color:#a8b3c7">Loading scanner + optimizer research...</p>`;

    try {
      const res = await fetch("/static/research/market_intelligence_latest.json?ts=" + Date.now());
      const data = await res.json();

      const tradeReady = data.trade_ready || [];
      const extended = data.extended_wait || [];
      const scannerTop = data.scanner_top || [];
      const best = data.best_strategy || {};

      panel.innerHTML = `
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px">
          <div>
            <h1 style="margin:0;font-size:34px">🧠 Market Intelligence</h1>
            <p style="color:#a8b3c7;margin-top:8px">Research-only scanner. Does not control live trades.</p>
            <p style="color:#7c8aa5;font-size:13px">Updated: ${safe(data.updated_at)}</p>
          </div>
          <button class="intel-close" id="ponderIntelClose">Close</button>
        </div>

        <div class="intel-grid">
          <div class="intel-card">
            <h3>Trade-Friendly Setups</h3>
            <div class="big">${tradeReady.length}</div>
            <div style="color:#a8b3c7;font-size:13px">Healthy or pullback zones</div>
          </div>
          <div class="intel-card">
            <h3>Extended / Wait</h3>
            <div class="big">${extended.length}</div>
            <div style="color:#a8b3c7;font-size:13px">Strong, but risky to chase</div>
          </div>
          <div class="intel-card">
            <h3>Best Research Config</h3>
            <div class="big">${safe(best.win_rate)}%</div>
            <div style="color:#a8b3c7;font-size:13px">Win rate from optimizer</div>
          </div>
        </div>

        ${table("✅ Trade-Friendly / Pullback Setups", tradeReady)}
        ${table("⚠️ Strong but Extended / Wait", extended)}
        ${table("📡 Scanner Top 15", scannerTop)}

        <h2>🧪 Best Strategy Research</h2>
        <pre style="background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);padding:16px;border-radius:16px;white-space:pre-wrap">${JSON.stringify(best, null, 2)}</pre>
      `;

      document.getElementById("ponderIntelClose").onclick = () => panel.style.display = "none";
    } catch (e) {
      panel.innerHTML = `
        <h1>🧠 Market Intelligence</h1>
        <p style="color:#ffb4b4">No research file loaded yet.</p>
        <p>Run:</p>
        <pre style="background:rgba(255,255,255,.05);padding:16px;border-radius:16px">python3 research_pipeline_v1.py</pre>
      `;
    }
  }

  btn.onclick = function () {
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      loadIntel();
    }
  };
});
'''

if "PONDER INTELLIGENCE UI V2" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Intelligence UI v2 installed")
else:
    print("Already installed")
