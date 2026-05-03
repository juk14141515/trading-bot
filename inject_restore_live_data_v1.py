from pathlib import Path

file = Path("web_dashboard.py")
text = file.read_text()

if "PONDER_LIVE_RESTORE_V1" not in text:

    js = """
    <!-- PONDER_LIVE_RESTORE_V1 -->
    <script>
    async function ponderUpdate() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();

            if (!data) return;

            // Portfolio
            document.querySelectorAll('[data-portfolio]').forEach(e => {
                e.innerText = "$" + (data.portfolio_value || 0).toLocaleString();
            });

            // Buying power
            document.querySelectorAll('[data-buying-power]').forEach(e => {
                e.innerText = "$" + (data.buying_power || 0).toLocaleString();
            });

            // P/L
            document.querySelectorAll('[data-pl]').forEach(e => {
                e.innerText = "$" + (data.open_pl || 0).toLocaleString();
            });

            // Command bar
            const chips = document.querySelectorAll('.pp-command-chip');
            if (chips.length >= 4) {
                chips[1].innerText = "Market: " + (data.market || "--");
                chips[2].innerText = "Health: " + (data.health || "--");
                chips[3].innerText = "P/L: $" + (data.open_pl || 0);
            }

        } catch (err) {
            console.log("Update error", err);
        }
    }

    setInterval(ponderUpdate, 5000);
    ponderUpdate();
    </script>
    """

    text = text.replace("</body>", js + "\n</body>")
    file.write_text(text)
    print("✅ Live data restore injected")
else:
    print("Already installed")
