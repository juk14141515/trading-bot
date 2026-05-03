from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_rotation_ui_v1").write_text(text)

ADD = r'''

// === PONDER ROTATION ENGINE UI V1 ===
window.addEventListener("load", function () {
  if (window.__ponderRotationUIV1) return;
  window.__ponderRotationUIV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    #ponderRotationBtn {
      position: fixed;
      right: 22px;
      top: 660px;
      z-index: 100000;
      width: 48px;
      height: 48px;
      border-radius: 16px;
      border: 1px solid rgba(124,255,178,.32);
      background: rgba(8,12,24,.95);
      color: white;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 14px 32px rgba(0,0,0,.38);
    }

    #ponderRotationPanel {
      display: none;
      position: fixed;
      inset: 58px 34px 34px 260px;
      z-index: 100000;
      overflow: auto;
      padding: 26px;
      border-radius: 26px;
      background:
        radial-gradient(circle at 10% 0%, rgba(124,255,178,.10), transparent 28%),
        radial-gradient(circle at 90% 0%, rgba(255,190,120,.08), transparent 30%),
        rgba(5,8,18,.98);
      border: 1px solid rgba(124,255,178,.20);
      box-shadow: 0 28px 90px rgba(0,0,0,.65);
      color: white;
      font-family: Arial, sans-serif;
    }

    .rotation-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }

    .rotation-card {
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,.045);
      border: 1px solid rgba(255,255,255,.08);
    }

    .rotation-card h3 {
      margin: 0 0 8px;
      color: #a8b3c7;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .05em;
    }

    .rotation-big {
      font-size: 25px;
      font-weight: 900;
    }

    .rotation-table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 24px;
      font-size: 13px;
    }

    .rotation-table th,
    .rotation-table td {
      padding: 10px;
      border-bottom: 1px solid rgba(255,255,255,.075);
      text-align: left;
      vertical-align: top;
    }

    .rotation-table th {
      color: #a8b3c7;
      font-size: 12px;
      text-transform: uppercase;
    }

    .rotation-close {
      padding: 10px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.06);
      color: white;
      cursor: pointer;
      font-weight: 800;
    }

    @media (max-width: 900px) {
      #ponderRotationPanel { inset: 20px; }
      .rotation-grid { grid-template-columns: 1fr; }
    }
  `;
  document.head.appendChild(style);

  const btn = document.createElement("button");
  btn.id = "ponderRotationBtn";
  btn.innerHTML = "🔄";
  btn.title = "Rotation Engine";
  document.body.appendChild(btn);

  const panel = document.createElement("div");
  panel.id = "ponderRotationPanel";
  document.body.appendChild(panel);

  function safe(x) {
    if (x === undefined || x === null || Number.isNaN(x)) return "--";
    return x;
  }

  function scoreColor(x) {
    const n = Number(x);
    if (n >= 70) return "color:#86ff9d";
    if (n >= 60) return "color:#ffd36d";
    return "color:#a8b3c7";
  }

  function row(x) {
    return `
      <tr>
        <td><strong>${safe(x.sell_symbol)}</strong></td>
        <td>➡️</td>
        <td><strong>${safe(x.buy_symbol)}</strong></td>
        <td style="${scoreColor(x.rotation_score)};font-weight:900">${safe(x.rotation_score)}</td>
        <td>${safe(x.action)}</td>
        <td>${safe(x.sell_pressure)}/100</td>
        <td>${safe(x.buy_score)}</td>
        <td>${safe(x.entry_zone)}</td>
        <td>${(x.why || []).join("<br>")}</td>
      </tr>
    `;
  }

  async function loadRotation() {
    panel.style.display = "block";
    panel.innerHTML = `<h1>🔄 Rotation Engine</h1><p style="color:#a8b3c7">Loading rotation research...</p>`;

    try {
      const res = await fetch("/static/research/rotation_engine_latest.json?ts=" + Date.now());
      const data = await res.json();
      const top = data.top_rotation || {};
      const summary = data.summary || {};
      const rotations = data.rotation_suggestions || [];

      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:18px;align-items:flex-start">
          <div>
            <h1 style="margin:0;font-size:34px">🔄 Rotation Engine</h1>
            <p style="color:#a8b3c7;margin-top:8px">Research-only capital rotation layer. Does not place trades.</p>
            <p style="color:#7c8aa5;font-size:13px">Updated: ${safe(data.updated_at)}</p>
          </div>
          <button class="rotation-close" id="ponderRotationClose">Close</button>
        </div>

        <div class="rotation-grid">
          <div class="rotation-card">
            <h3>Top Rotation</h3>
            <div class="rotation-big">${safe(top.sell_symbol)} ➜ ${safe(top.buy_symbol)}</div>
            <div style="color:#a8b3c7;font-size:13px">${safe(top.action)}</div>
          </div>
          <div class="rotation-card">
            <h3>Rotation Score</h3>
            <div class="rotation-big" style="${scoreColor(top.rotation_score)}">${safe(top.rotation_score)}</div>
            <div style="color:#a8b3c7;font-size:13px">Sell pressure + buy quality</div>
          </div>
          <div class="rotation-card">
            <h3>Rotations Found</h3>
            <div class="rotation-big">${safe(summary.rotations_found)}</div>
            <div style="color:#a8b3c7;font-size:13px">Research only</div>
          </div>
        </div>

        <h2>Rotation Suggestions</h2>
        <table class="rotation-table">
          <thead>
            <tr>
              <th>Sell</th>
              <th></th>
              <th>Buy</th>
              <th>Score</th>
              <th>Action</th>
              <th>Sell Pressure</th>
              <th>Buy Score</th>
              <th>Entry Zone</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>${rotations.map(row).join("")}</tbody>
        </table>

        <h2>Notes</h2>
        <div class="rotation-card">
          <ul>${(data.notes || []).map(n => `<li>${n}</li>`).join("")}</ul>
        </div>
      `;

      document.getElementById("ponderRotationClose").onclick = () => panel.style.display = "none";
    } catch (e) {
      panel.innerHTML = `
        <h1>🔄 Rotation Engine</h1>
        <p style="color:#ffb4b4">No rotation file found.</p>
        <pre>python3 rotation_engine_v1.py</pre>
      `;
    }
  }

  btn.onclick = function () {
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      loadRotation();
    }
  };
});
'''

if "PONDER ROTATION ENGINE UI V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Rotation Engine UI installed")
else:
    print("Already installed")
