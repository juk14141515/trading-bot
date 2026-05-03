from pathlib import Path

p = Path("static/ponder_ui.js")

if not p.exists():
    raise SystemExit("❌ static/ponder_ui.js not found")

text = p.read_text()
backup = p.with_suffix(".js.bak_alive_v1")
backup.write_text(text)

ADDON = r'''

// === PONDER ALIVE UI V1 ===
(function () {
  if (window.__ponderAliveV1) return;
  window.__ponderAliveV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    @keyframes ponderPulse {
      0% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.035); opacity: .92; }
      100% { transform: scale(1); opacity: 1; }
    }

    @keyframes ponderGlow {
      0% { box-shadow: 0 0 0 rgba(100,255,160,0); }
      50% { box-shadow: 0 0 24px rgba(100,255,160,.22); }
      100% { box-shadow: 0 0 0 rgba(100,255,160,0); }
    }

    .ponder-alive-card {
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }

    .ponder-alive-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 18px 42px rgba(0,0,0,.32), 0 0 24px rgba(120,180,255,.16);
      border-color: rgba(130,255,170,.35) !important;
    }

    .ponder-live-pulse {
      animation: ponderPulse 2.4s ease-in-out infinite;
    }

    .ponder-positive {
      color: #7CFFB2 !important;
      text-shadow: 0 0 14px rgba(124,255,178,.35);
    }

    .ponder-negative {
      color: #FF8A8A !important;
      text-shadow: 0 0 14px rgba(255,138,138,.28);
    }
  `;
  document.head.appendChild(style);

  function enhanceCards() {
    document.querySelectorAll(".card, .metric-card, .panel").forEach((card, i) => {
      card.classList.add("ponder-alive-card");

      if (!card.dataset.ponderAnimated) {
        card.dataset.ponderAnimated = "1";
        card.style.opacity = "0";
        card.style.transform = "translateY(10px)";
        setTimeout(() => {
          card.style.transition = "all .35s ease";
          card.style.opacity = "1";
          card.style.transform = "translateY(0)";
        }, i * 45);
      }
    });
  }

  function colorValues() {
    document.querySelectorAll(".value, h2, h3, .card div").forEach(el => {
      const text = (el.innerText || "").trim();
      if (!text.includes("$") && !text.includes("%")) return;

      const num = parseFloat(text.replace(/[^0-9.-]/g, ""));
      if (Number.isNaN(num)) return;

      if (text.includes("$") && num > 0) el.classList.add("ponder-positive");
      if (text.includes("$") && num < 0) el.classList.add("ponder-negative");
    });
  }

  function pulseLive() {
    document.querySelectorAll("div, span").forEach(el => {
      const t = (el.innerText || "").trim();
      if (t === "LIVE" || t.includes("MARKET OPEN") || t.includes("AI Health")) {
        el.classList.add("ponder-live-pulse");
      }
    });
  }

  function tickPulseValues() {
    document.querySelectorAll(".value").forEach(el => {
      el.style.transition = "transform .22s ease";
      el.style.transform = "scale(1.035)";
      setTimeout(() => {
        el.style.transform = "scale(1)";
      }, 160);
    });
  }

  enhanceCards();
  colorValues();
  pulseLive();

  setInterval(() => {
    colorValues();
    pulseLive();
    tickPulseValues();
  }, 5000);
})();
'''

if "PONDER ALIVE UI V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADDON + "\n")
    print("✅ Added Ponder Alive UI v1 to static/ponder_ui.js")
else:
    print("Already installed")

print("DONE")
