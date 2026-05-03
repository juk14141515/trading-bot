import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, url_for

LOG_FILE = Path(__file__).resolve().parents[1] / "log.txt"
from shadow_evaluator import evaluate_shadow_ideas, summarize_learning, load_ideas


CLOUD_PROMPT = """Continue work on Ponder Invest AI.

Use this direction:
{task_prompt}

Current live context:
{snapshot_json}

Priority:
Keep the new Flask dashboard modular and consistent. Do not change live trading logic. Add dashboard/UI/planning features only unless I explicitly ask for backend trading changes.
Important: Codex Cloud cannot automatically see this local desktop chat. It works from a GitHub-connected repo in a cloud sandbox, so the best handoff is: repo + Cloud Prompt + Snapshot.

The Build Plan page is your “direction of conversation” page. The Snapshot page is your “current system state” page. Together, those are the handoff package."""


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["APP_NAME"] = "Ponder Invest AI"
    app.config["APP_MODE"] = os.getenv("PONDER_MODE", "research-only")
    app.config["DASHBOARD_PASSWORD"] = os.getenv("PONDER_DASH_PASSWORD")

    @app.get("/")
    def home():
        return render_template("dashboard.html", app_name=app.config["APP_NAME"], page_title="Dashboard", cards=_research_cards())


    @app.get("/history")
    def history():
        return render_template("history.html", app_name=app.config["APP_NAME"], page_title="History", log_lines=_read_recent_logs(80))

    @app.get("/settings")
    def settings():
        return render_template("settings.html", app_name=app.config["APP_NAME"], page_title="Settings")

    @app.get("/build-plan")
    def build_plan():
        return render_template("build_plan.html", app_name=app.config["APP_NAME"], page_title="Build Plan", targets=[
            "secure login and consistent UI",
            "card-based research views",
            "larger live equity/capital graphs",
            "module health and copy snapshot",
        ])


    @app.get("/research")
    def research():
        summary = summarize_learning()
        ideas = load_ideas()
        return render_template("research.html", app_name=app.config["APP_NAME"], page_title="Research Hub", summary=summary, ideas=ideas)

    @app.post("/api/research/evaluate")
    def api_evaluate():
        stats = evaluate_shadow_ideas()
        return jsonify({"pending_loaded": stats.pending_loaded, "evaluated_now": stats.evaluated_now, "skipped_too_new": stats.skipped_too_new, "errors": stats.errors})

    @app.get("/api/research/learning")
    def api_learning():
        return jsonify({"summary": summarize_learning(), "ideas": [_public_idea(i) for i in load_ideas()]})

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "app": app.config["APP_NAME"],
                "mode": app.config["APP_MODE"],
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
        )

    @app.get("/snapshot")
    def snapshot():
        return jsonify(_build_snapshot())

    @app.get("/debug-snapshot")
    def debug_snapshot():
        return render_template(
            "debug_snapshot.html",
            app_name=app.config["APP_NAME"],
            page_title="Debug Snapshot",
            cloud_prompt=CLOUD_PROMPT,
            snapshot_url=url_for("snapshot"),
            snapshot_json=_build_snapshot(),
        )

    return app


def _read_recent_logs(limit: int = 30) -> list[str]:
    if not LOG_FILE.exists():
        return ["No log file found yet."]

    with LOG_FILE.open("r", encoding="utf-8") as f:
        lines = [line.rstrip() for line in f.readlines() if line.strip()]
    return lines[-limit:] if lines else ["No log activity yet."]


def _research_cards() -> list[dict[str, str]]:
    return [
        {
            "title": "Module Health",
            "content": "All research modules loaded. Trading execution is disabled by design.",
        },
        {
            "title": "Security Posture",
            "content": "Credentials are environment-driven; no secrets are embedded in templates.",
        },
        {
            "title": "Accessibility",
            "content": "Palette selected for strong contrast and colorblind-safe chart defaults.",
        },
    ]


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)


def _build_snapshot() -> dict:
    return {
        "title": "Ponder Invest AI dashboard continuation",
        "safe_files_first": [
            "new_ponder_site/app.py",
            "new_ponder_site/templates/",
            "new_ponder_site/static/style.css",
            "new_ponder_site/static/site/js/app.js",
        ],
        "task_prompt": (
            "You are continuing work on Ponder Invest AI, a personal research-only trading bot dashboard. "
            "Keep the new Flask app in new_ponder_site modular and consistent. "
            "Do not change live trading logic unless explicitly requested. "
            "Prioritize secure access, reusable templates, readable research cards, module health, "
            "snapshot handoff, larger graphs, Ponder branding, colorblind accessibility, "
            "and future research-only modules."
        ),
    }


def _public_idea(i: dict) -> dict:
    return {
        "id": i.get("id", "unknown"),
        "type": i.get("type", "unknown"),
        "action": i.get("action", "Pending"),
        "status": i.get("status", "pending"),
        "result": i.get("result") or "Pending",
        "alpha": i.get("alpha"),
        "outcome": i.get("outcome") if i.get("outcome") != "unresolved" else "Not evaluated yet",
        "from_symbol": i.get("from_symbol") or "-",
        "to_symbol": i.get("to_symbol") or "-",
        "created_at": i.get("created_at"),
    }
