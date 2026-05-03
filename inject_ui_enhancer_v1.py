from pathlib import Path

p = Path("web_dashboard.py")
text = p.read_text()

BLOCK = """
<!-- PONDER UI ENHANCER V1 -->
<script>
window.addEventListener("load", () => {

  // Animate cards
  document.querySelectorAll(".card").forEach((card, i) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";
    setTimeout(() => {
      card.style.transition = "all 0.5s ease";
      card.style.opacity = "1";
      card.style.transform = "translateY(0)";
    }, i * 80);
  });

  // Glow effect on P/L
  document.querySelectorAll(".value").forEach(v => {
    if (v.innerText.includes("$")) {
      v.style.textShadow = "0 0 12px rgba(0,255,140,0.5)";
    }
  });

  // Live pulse on market open
  const market = document.body.innerText.includes("MARKET OPEN");
  if (market) {
    const badge = document.querySelector("div");
    if (badge) {
      badge.style.animation = "pulse 2s infinite";
    }
  }

});

// Pulse animation
const style = document.createElement("style");
style.innerHTML = `
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}`;
document.head.appendChild(style);

</script>
"""

if "PONDER UI ENHANCER V1" not in text:
    text = text.replace("</body>", BLOCK + "\n</body>")
    p.write_text(text)
    print("✅ UI enhancer injected")
else:
    print("Already installed")
