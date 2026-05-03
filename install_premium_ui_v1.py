from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_premium_v1").write_text(text)

ADD = r'''

// === PONDER PREMIUM UI V1 ===
window.addEventListener("load", function () {
  if (window.__ponderPremiumV1) return;
  window.__ponderPremiumV1 = true;

  const style = document.createElement("style");
  style.innerHTML = `
    body {
      letter-spacing: -0.01em;
    }

    h1 {
      letter-spacing: -0.04em;
    }

    .premium-card {
      transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease !important;
    }

    .premium-card:hover {
      transform: translateY(-3px) !important;
      border-color: rgba(150, 170, 255, .42) !important;
      box-shadow: 0 18px 45px rgba(0,0,0,.34) !important;
    }

    .premium-primary {
      border-color: rgba(130,255,170,.28) !important;
      background: linear-gradient(180deg, rgba(22,29,49,.96), rgba(14,18,34,.96)) !important;
    }

    .premium-primary::after {
      content: "";
      position: absolute;
      left: 22px;
      right: 22px;
      top: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(130,255,170,.55), transparent);
    }

    #ponder_ai_health_badge {
      opacity: .72;
      transform: scale(.92);
    }

    #ponder_ai_health_badge:hover {
      opacity: 1;
      transform: scale(1);
    }
  `;
  document.head.appendChild(style);

  const important = ["Portfolio Value", "Buying Power", "Open P/L", "Account Status"];

  document.querySelectorAll("div").forEach(el => {
    const txt = el.innerText || "";
    const r = el.getBoundingClientRect();

    if (r.width > 180 && r.height > 90 && important.some(x => txt.includes(x))) {
      el.classList.add("premium-card", "premium-primary");
      el.style.position = "relative";
      el.style.overflow = "hidden";
    } else if (r.width > 180 && r.height > 90 && (
      txt.includes("Win Rate") ||
      txt.includes("Capital Deployed") ||
      txt.includes("Bot Actions") ||
      txt.includes("Scanner Events") ||
      txt.includes("Rotations") ||
      txt.includes("Adaptive Events")
    )) {
      el.classList.add("premium-card");
    }
  });
});
'''

if "PONDER PREMIUM UI V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Premium UI v1 installed")
else:
    print("Already installed")
