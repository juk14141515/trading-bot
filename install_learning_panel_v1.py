from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_learning_panel_v1").write_text(text)

ADD = r'''

// === PONDER LEARNING PANEL V1 ===
window.addEventListener("load", function () {
  if (window.__ponderLearningPanelV1) return;
  window.__ponderLearningPanelV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    #ponderLearningBtn {
      position: fixed;
      right: 22px;
      top: 480px;
      z-index: 100000;
      width: 48px;
      height: 48px;
      border-radius: 16px;
      border: 1px solid rgba(124,255,178,.28);
      background: rgba(8,12,24,.95);
      color: white;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 14px 32px rgba(0,0,0,.38);
    }

    #ponderLearningPanel {
      display: none;
      position: fixed;
      inset: 58px 34px 34px 260px;
      z-index: 100000;
      overflow: auto;
      padding: 26px;
      border-radius: 26px;
      background:
        radial-gradient(circle at 10% 0%, rgba(124,255,178,.08), transparent 28%),
        radial-gradient(circle at 90% 0%, rgba(120,160,255,.08), transparent 30%),
        rgba(5,8,18,.98);
      border: 1px solid rgba(124,255,178,.18);
      box-shadow: 0 28px 90px rgba(0,0,0,.65);
      color: white;
      font-family: Arial, sans-serif;
    }

    .learn-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }

    .learn-card {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,.045);
      border: 1px solid rgba(255,255,255,.08);
    }

    .learn-card h3 {
      margin: 0 0 8px;
      color: #a8b3c7;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .05em;
    }

    .learn-big {
      font-size: 25px;
      font-weight: 900;
    }

    .learn-good { color: #86ff9d; }
    .learn-warn { color: #ffe66d; }
    .learn-bad { color: #ff8b8b; }
    .learn-info { color: #9db7ff; }

    .learn-table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 24px;
      font-size: 13px;
    }

    .learn-table th,
    .learn-table td {
      padding: 10px;
      border-bottom: 1px solid rgba(255,255,255,.075);
      text-align: left;
    }

    .learn-table th {
      color: #a8b3c7;
      font-size: 12px;
      text-transform: uppercase;
    }

    .learn-section {
      margin-top: 24px;
    }

    .learn-close {
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.06);
      color: white;
      cursor: pointer;
      font-weight: 800;
    }

    @media (max-width: 900px) {
      #ponderLearningPanel { inset: 20px; }
      .learn-grid { grid-template-columns: 1fr; }
    }
  `;
  document.head.appendChild(style);

  const btn = document.createElement("button");
  btn.id = "ponderLearningBtn";
  btn.innerHTML = "📚";
  btn.title = "Learning Panel";
  document.body.appendChild(btn);

  const panel = document.createElement("div");
  panel.id = "ponderLearningPanel";
  document.body.appendChild(panel);

  function moneyGuess(txt, label) {
    const re = new RegExp(label + "[\\s\\S]{0,120}?\\$([0-9,]+\\.?[0-9]*)", "i");
    const m = txt.match(re);
    return m ? parseFloat(m[1].replace(/,/g, "")) : null;
  }

  function safe(x) {
    if (x === undefined || x === null || Number.isNaN(x)) return "--";
    return x;
  }

  function setupRow(x) {
    return `
      <tr>
        <td>${safe(x.symbols_group)}</td>
        <td>${safe(x.threshold)}</td>
        <td>${safe(x.take_profit_pct)}%</td>
        <td>${safe(x.stop_loss_pct)}%</td>
        <td>${safe(x.max_hold_minutes)}m</td>
        <td>${safe(x.win_rate)}%</td>
        <td>${safe(x.avg_pnl_pct)}%</td>
        <td>${safe(x.trades)}</td>
      </tr>
    `;
  }

  function scannerRow(x) {
    return `
      <tr>
        <td><strong>${safe(x.symbol)}</strong></td>
        <td>${safe(x.final_score)}</td>
        <td>${safe(x.entry_zone)}</td>
        <td>${safe(x.pullback_from_sma5_pct)}%</td>
        <td>${safe(x.extension_from_sma20_pct)}%</td>
        <td>${safe(x.label)}</td>
      </tr>
    `;
  }

  async function loadLearning() {
    panel.style.display = "block";
    panel.innerHTML = `<h1>📚 Ponder Learning Panel</h1><p style="color:#a8b3c7">Loading research + dashboard context...</p>`;

    const bodyText = document.body.innerText || "";
    const buyingPower = moneyGuess(bodyText, "Buying Power");
    const portfolioValue = moneyGuess(bodyText, "Portfolio Value");
    const openPL = moneyGuess(bodyText, "Open P/L");

    let cashUtil = null;
    if (buyingPower && portfolioValue) {
      cashUtil = Math.max(0, Math.min(100, ((portfolioValue - buyingPower) / portfolioValue) * 100));
    }

    try {
      const res = await fetch("/static/research/market_intelligence_latest.json?ts=" + Date.now());
      const data = await res.json();

      const best = data.best_strategy || {};
      const optimizerTop = data.optimizer_top || [];
      const tradeReady = data.trade_ready || [];
      const extended = data.extended_wait || [];

      const noRealSellsNote = `
        This panel sees closed net P/L as $0 / no real closed-trade learning yet if your dashboard still shows no closed sells.
        Keep optimizer/scanner in research mode until live sell data exists.
      `;

      let utilizationLabel = "Unknown";
      let utilizationClass = "learn-info";
      if (cashUtil !== null) {
        if (cashUtil < 35) {
          utilizationLabel = "Underutilized";
          utilizationClass = "learn-warn";
        } else if (cashUtil < 75) {
          utilizationLabel = "Healthy";
          utilizationClass = "learn-good";
        } else {
          utilizationLabel = "Aggressive";
          utilizationClass = "learn-bad";
        }
      }

      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start">
          <div>
            <h1 style="margin:0;font-size:34px">📚 Ponder Learning Panel</h1>
            <p style="color:#a8b3c7;margin-top:8px">Research-only learning dashboard. No live-trade control.</p>
            <p style="color:#7c8aa5;font-size:13px">Updated: ${safe(data.updated_at)}</p>
          </div>
          <button class="learn-close" id="ponderLearningClose">Close</button>
        </div>

        <div class="learn-grid">
          <div class="learn-card">
            <h3>Best Strategy Win Rate</h3>
            <div class="learn-big learn-good">${safe(best.win_rate)}%</div>
            <div style="color:#a8b3c7;font-size:13px">Optimizer research only</div>
          </div>

          <div class="learn-card">
            <h3>Trade-Friendly Setups</h3>
            <div class="learn-big learn-info">${tradeReady.length}</div>
            <div style="color:#a8b3c7;font-size:13px">Healthy / pullback zones</div>
          </div>

          <div class="learn-card">
            <h3>Cash Utilization</h3>
            <div class="learn-big ${utilizationClass}">${cashUtil === null ? "--" : cashUtil.toFixed(1) + "%"}</div>
            <div style="color:#a8b3c7;font-size:13px">${utilizationLabel}</div>
          </div>

          <div class="learn-card">
            <h3>Closed Sell Learning</h3>
            <div class="learn-big learn-warn">Limited</div>
            <div style="color:#a8b3c7;font-size:13px">Need more real exits</div>
          </div>
        </div>

        <div class="learn-section">
          <h2>🧠 Learning Notes</h2>
          <div class="learn-card">
            <p><strong>No real sells yet:</strong> ${noRealSellsNote}</p>
            <p><strong>Unused cash / buying power:</strong> If utilization is low, the bot may be too conservative, blocked by max positions, or lacking quality candidates.</p>
            <p><strong>Overnight risk:</strong> Add an overnight scanner/news analyzer before letting the bot act on premarket sentiment.</p>
          </div>
        </div>

        <div class="learn-section">
          <h2>🧪 Best Strategy Config</h2>
          <div class="learn-card">
            <pre style="white-space:pre-wrap;margin:0">${JSON.stringify(best, null, 2)}</pre>
          </div>
        </div>

        <div class="learn-section">
          <h2>🏆 Top Optimizer Setups</h2>
          <table class="learn-table">
            <thead>
              <tr>
                <th>Group</th><th>Threshold</th><th>TP</th><th>SL</th><th>Hold</th><th>Win</th><th>Avg P/L</th><th>Trades</th>
              </tr>
            </thead>
            <tbody>${optimizerTop.map(setupRow).join("")}</tbody>
          </table>
        </div>

        <div class="learn-section">
          <h2>✅ Trade-Friendly Scanner Setups</h2>
          <table class="learn-table">
            <thead>
              <tr>
                <th>Symbol</th><th>Score</th><th>Entry Zone</th><th>Pullback</th><th>Extension</th><th>Label</th>
              </tr>
            </thead>
            <tbody>${tradeReady.map(scannerRow).join("")}</tbody>
          </table>
        </div>

        <div class="learn-section">
          <h2>⚠️ Extended / Do Not Chase</h2>
          <table class="learn-table">
            <thead>
              <tr>
                <th>Symbol</th><th>Score</th><th>Entry Zone</th><th>Pullback</th><th>Extension</th><th>Label</th>
              </tr>
            </thead>
            <tbody>${extended.map(scannerRow).join("")}</tbody>
          </table>
        </div>

        <div class="learn-section">
          <h2>🌙 Overnight Analyzer Roadmap</h2>
          <div class="learn-card">
            <p><strong>Next module:</strong> overnight_market_brief_v1.py</p>
            <p>It should collect: futures direction, major index ETFs, top premarket movers, earnings, Fed/economic calendar events, sector news, and high-impact headlines.</p>
            <p>Output should save to <code>static/research/overnight_brief_latest.json</code> and appear here before market open.</p>
          </div>
        </div>
      `;

      document.getElementById("ponderLearningClose").onclick = () => panel.style.display = "none";
    } catch (e) {
      panel.innerHTML = `
        <h1>📚 Ponder Learning Panel</h1>
        <p style="color:#ffb4b4">No research data found.</p>
        <pre>python3 research_pipeline_v1.py</pre>
      `;
    }
  }

  btn.onclick = function () {
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      loadLearning();
    }
  };
});
'''

if "PONDER LEARNING PANEL V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Learning panel installed")
else:
    print("Already installed")
