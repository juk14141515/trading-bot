from pathlib import Path
from datetime import datetime
import glob
import shutil

WEB = Path("web_dashboard.py")

# 1) Find latest backup made before the bad mobile/login injection
backups = sorted(
    glob.glob("web_dashboard_backup_mobile_login_*.py"),
    reverse=True
)

if not backups:
    raise SystemExit("No mobile-login backup found. Cannot safely repair.")

backup = Path(backups[0])

# 2) Restore known-good dashboard
repair_backup = Path(f"web_dashboard_broken_before_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
shutil.copy(WEB, repair_backup)
shutil.copy(backup, WEB)

text = WEB.read_text()

# 3) Safe mobile-only CSS injection
mobile_css = r'''
            @media (max-width: 760px) {
                .container {
                    padding: 12px !important;
                    max-width: 100% !important;
                }

                .header {
                    position: sticky;
                    top: 0;
                    z-index: 20;
                    background: rgba(3, 7, 18, 0.96);
                    backdrop-filter: blur(12px);
                    padding: 12px;
                    margin-bottom: 14px;
                    border-bottom: 1px solid rgba(255,255,255,0.08);
                }

                .brand {
                    font-size: 28px !important;
                }

                .subtitle {
                    font-size: 13px !important;
                }

                .grid,
                .grid-2 {
                    grid-template-columns: 1fr !important;
                    gap: 12px !important;
                }

                .card {
                    padding: 16px !important;
                    border-radius: 18px !important;
                }

                .big {
                    font-size: 25px !important;
                }

                table {
                    display: block;
                    overflow-x: auto;
                    white-space: nowrap;
                }

                th, td {
                    font-size: 12px !important;
                    padding: 10px 8px !important;
                }

                pre {
                    font-size: 12px !important;
                    max-height: 220px !important;
                }
            }
'''

if mobile_css not in text:
    text = text.replace("</style>", mobile_css + "\n        </style>", 1)

# 4) Add viewport safely
if 'name="viewport"' not in text:
    text = text.replace(
        '<meta http-equiv="refresh" content="5">',
        '<meta http-equiv="refresh" content="5">\n        <meta name="viewport" content="width=device-width, initial-scale=1">'
    )

WEB.write_text(text)

print("✅ Dashboard restored from:", backup)
print("✅ Broken version saved as:", repair_backup)
print("✅ Safe mobile CSS reapplied")
print("Now run:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
