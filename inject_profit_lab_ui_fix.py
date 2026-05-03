import os
from datetime import datetime

FILE = "templates/profit_lab.html"

CSS_BLOCK = """
<!-- PONDER UI FIX INJECT -->
<style id="ponder-ui-fix">
body::before {
    content: "";
    position: fixed;
    left: 0;
    top: 0;
    width: 140px;
    height: 100%;
    background: linear-gradient(180deg, #050c1a, #020617);
    z-index: 5;
    pointer-events: none;
}

.sidebar {
    position: relative;
    z-index: 10;
}

.main-content {
    position: relative;
    z-index: 10;
}

canvas, .chart-container {
    position: relative;
    z-index: 2;
}

body {
    overflow-x: hidden;
}
</style>
"""

def main():
    if not os.path.exists(FILE):
        print("ERROR: profit_lab.html not found")
        return

    with open(FILE, "r") as f:
        content = f.read()

    # Prevent duplicate inject
    if "ponder-ui-fix" in content:
        print("SKIP: UI fix already injected")
        return

    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{FILE}.bak_ui_fix_{timestamp}"
    with open(backup, "w") as f:
        f.write(content)

    print(f"BACKUP CREATED: {backup}")

    # Inject before </body>
    if "</body>" in content:
        content = content.replace("</body>", CSS_BLOCK + "\n</body>")
    else:
        content += CSS_BLOCK

    with open(FILE, "w") as f:
        f.write(content)

    print("DONE: UI fix injected safely")

if __name__ == "__main__":
    main()
