from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_market_intel_v1").write_text(text)

ADD = r'''

// === PONDER MARKET INTELLIGENCE DASHBOARD V1 ===
window.addEventListener("load", function () {
  if (window.__ponderMarketIntelV1) return;
  window.__ponderMarketIntelV1 = true;

  const btn = document.createElement("button");
  btn.innerHTML = "🧠";
  btn.title = "Market Intelligence";
  btn.style.cssText = `
    position:fixed; right:22px; top:420px; z-index:100000;
    width:44px; height:44px; border-radius:14px;
    border:1px solid rgba(140,160,255,.35);
    background:rgba(18,24,45,.92); color:white;
    cursor:pointer; font-size:18px;
  `;
  document.body.appendChild(btn);

  const panel = document.createElement("div");
  panel.id = "ponderMarketIntelPanel";
  panel.style.cssText = `
    display:none; position:fixed; inset:72px 36px 36px 260px;
    z-index:100000; overflow:auto; padding:24px;
    border-radius:24px; border:1px solid rgba(140,160,255,.25);
    background:rgba(8,12,24,.97); color:white;
    box-shadow:0 24px 70px rgba(0,0,0,.55);
    font-family:Arial,sans-serif;
  `;
  document.body.appendChild(panel);

  function row(x) {
    return `
      <tr>
        <td>${x.symbol ?? ""}</td>
        <td>${x.final_score ?? ""}</td>
        <td>${x.entry_zone ?? ""}</td>
        <td>${x.pullback_from_sma5_pct ?? ""}%</td>
        <td>${x.extension_from_sma20_pct ?? ""}%</td>
        <td>${x.label ?? ""}</td>
      </tr>
    `;
  }

  async function loadIntel() {
    panel.innerHTML = "<h2>🧠 Market Intelligence</h2><p>Loading research data...</p>";
    try {
      const res = await fetch("/static/research/market_intelligence_latest.json?ts=" + Date.now());
      const data = await res.json();

      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:16px;align-items:center">
          <div>
            <h1 style="margin:0">🧠 Market Intelligence</h1>
            <p style="color:#a8b3c7">Updated: ${data.updated_at}</p>
          </div>
          <button id="closeIntel" style="padding:10px 14px;border-radius:12px;background:#111827;color:white;border:1px solid #334155;cursor:pointer">Close</button>
        </div>

        <h2>✅ Trade-Friendly / Pullback Setups</h2>
        <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
          <thead><tr><th>Symbol</th><th>Score</th><th>Entry Zone</th><th>Pullback</th><th>Extension</th><th>Label</th></tr></thead>
          <tbody>${(data.trade_ready || []).map(row).join("")}</tbody>
        </table>

        <h2>⚠️ Strong but Extended</h2>
        <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
          <thead><tr><th>Symbol</th><th>Score</th><th>Entry Zone</th><th>Pullback</th><th>Extension</th><th>Label</th></tr></thead>
          <tbody>${(data.extended_wait || []).map(row).join("")}</tbody>
        </table>

        <h2>🧪 Best Strategy Research</h2>
        <pre style="background:rgba(255,255,255,.05);padding:16px;border-radius:16px;white-space:pre-wrap">${JSON.stringify(data.best_strategy || {}, null, 2)}</pre>
      `;

      panel.querySelectorAll("td,th").forEach(e => {
        e.style.cssText = "padding:10px;border-bottom:1px solid rgba(255,255,255,.08);text-align:left";
      });

      document.getElementById("closeIntel").onclick = () => panel.style.display = "none";
    } catch (e) {
      panel.innerHTML = "<h2>Market Intelligence</h2><p>No research data found yet. Run <code>python3 research_pipeline_v1.py</code>.</p>";
    }
  }

  btn.onclick = function () {
    panel.style.display = panel.style.display === "none" ? "block" : "none";
    if (panel.style.display === "block") loadIntel();
  };
});
'''

if "PONDER MARKET INTELLIGENCE DASHBOARD V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Market Intelligence dashboard installed")
else:
    print("Already installed")
