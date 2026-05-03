from pathlib import Path

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_soft_refresh_v1").write_text(text)

ADD = r'''

// === PONDER SOFT REFRESH V1 ===
window.addEventListener("load", function () {
  if (window.__ponderSoftRefreshV1) return;
  window.__ponderSoftRefreshV1 = true;

  async function softRefreshMain() {
    try {
      const res = await fetch(window.location.pathname + "?soft_ts=" + Date.now(), {
        cache: "no-store",
        credentials: "same-origin"
      });
      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, "text/html");

      const newContainer = doc.querySelector(".container");
      const oldContainer = document.querySelector(".container");

      if (!newContainer || !oldContainer) return;

      // Keep overlays/buttons/panels untouched. Only replace main dashboard content.
      oldContainer.innerHTML = newContainer.innerHTML;

      window.dispatchEvent(new Event("ponder-soft-refresh"));
    } catch (e) {
      console.log("Soft refresh skipped:", e);
    }
  }

  // Main and History pages only for now.
  const path = window.location.pathname;
  const canSoftRefresh = path === "/" || path === "/history";

  if (canSoftRefresh) {
    setInterval(softRefreshMain, path === "/history" ? 15000 : 5000);
  }
});
'''

if "PONDER SOFT REFRESH V1" not in text:
    p.write_text(text.rstrip() + "\n" + ADD + "\n")
    print("✅ Soft refresh installed")
else:
    print("Already installed")
