from pathlib import Path

APP = Path("new_ponder_site/app.py")
DASH = Path("new_ponder_site/templates/dashboard.html")

APP.with_suffix(".py.backup_snapshot_api_v1").write_text(APP.read_text())
DASH.with_suffix(".html.backup_snapshot_api_v1").write_text(DASH.read_text())

app = APP.read_text()

if '@app.route("/api/snapshot")' not in app:
    app = app.replace(
'''@app.route("/health")
def health():''',
'''@app.route("/api/snapshot")
@auth_required
def api_snapshot():
    return load_json("system_snapshot_latest.json")


@app.route("/health")
def health():'''
    )

APP.write_text(app)

dash = DASH.read_text()
dash = dash.replace(
    'fetch("/static/research/system_snapshot_latest.json?t=" + Date.now())',
    'fetch("/api/snapshot?t=" + Date.now())'
)

DASH.write_text(dash)

print("✅ Snapshot API route wired.")
