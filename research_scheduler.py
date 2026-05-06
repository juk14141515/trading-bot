"""Ponder Invest AI research scheduler.

Research-only orchestration layer for keeping dashboard intelligence fresh.

Safety guarantees:
- never imports bot.py
- never calls Alpaca/order APIs directly
- never places orders
- never edits live trading, risk, scoring, or execution logic
- only runs existing research scripts as subprocesses and writes a scheduler status JSON

Usage:
  python3 research_scheduler.py --mode inspect
  python3 research_scheduler.py --mode intraday
  python3 research_scheduler.py --mode after-close
  python3 research_scheduler.py --mode overnight
  python3 research_scheduler.py --mode full
  python3 research_scheduler.py --mode after-close --dry-run

Cron installer lives in scripts/install_research_scheduler_cron.sh.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_OUT = ROOT / "static" / "research"
OUT_FILE = RESEARCH_OUT / "research_scheduler_latest.json"
LOG_DIR = ROOT / "logs" / "research_scheduler"

PYTHON = os.getenv("PONDER_PYTHON", sys.executable or "python3")
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("PONDER_RESEARCH_JOB_TIMEOUT", "180"))
LONG_TIMEOUT_SECONDS = int(os.getenv("PONDER_RESEARCH_LONG_TIMEOUT", "900"))


@dataclass(frozen=True)
class Job:
    name: str
    script: str
    modes: tuple[str, ...]
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    required: bool = False
    reason: str = ""


JOBS: tuple[Job, ...] = (
    # Fresh market/dashboard intelligence. These are safe read-only research generators.
    Job("market_scanner", "market_scanner_v2.py", ("intraday", "after-close", "full"), reason="Refresh top candidates / scanner feed."),
    Job("market_regime", "market_regime_filter_v1.py", ("intraday", "after-close", "full"), reason="Refresh market regime card."),
    Job("sell_intelligence", "sell_intelligence_v1.py", ("intraday", "after-close", "full"), reason="Refresh sell/watch intelligence feed."),
    Job("rotation_engine", "rotation_engine_v3.py", ("intraday", "after-close", "full"), reason="Refresh rotation ideas; research-only."),
    Job("rotation_performance", "rotation_performance_tracker_v2.py", ("after-close", "overnight", "full"), reason="Evaluate rotation suggestions after outcomes update."),
    Job("capital_intelligence", "capital_intelligence_v1.py", ("intraday", "after-close", "full"), reason="Refresh capital/freshness dashboard feed."),

    # Live-shadow learning layer.
    Job("daytime_shadow_collector", "daytime_shadow_setup_collector.py", ("intraday", "after-close", "full"), reason="Collect current candidates into shadow setup log."),
    Job("setup_outcome_evaluator", "setup_outcome_evaluator.py", ("after-close", "overnight", "full"), timeout=LONG_TIMEOUT_SECONDS, reason="Evaluate logged shadow setups once market data is available."),
    Job("shadow_strategy_researcher", "shadow_strategy_researcher.py", ("after-close", "overnight", "full"), timeout=LONG_TIMEOUT_SECONDS, reason="Research setup quality from evaluated outcomes."),
    Job("shadow_execution", "shadow_execution_engine.py", ("intraday", "after-close", "overnight", "full"), reason="Simulate accepted/rejected shadow trades."),
    Job("shadow_live_comparison", "shadow_live_comparison_engine_v1.py", ("intraday", "after-close", "overnight", "full"), reason="Compare live trades vs shadow opportunities."),
    Job("shadow_capital_allocator", "shadow_capital_allocator_v2.py", ("intraday", "after-close", "overnight", "full"), reason="Refresh shadow-only capital allocation output."),

    # Snapshot/summary layers. These are dashboard-only.
    Job("system_snapshot", "system_snapshot.py", ("intraday", "after-close", "overnight", "full"), reason="Refresh system health snapshot."),
    Job("ai_summary", "ai_summary_layer_v1.py", ("after-close", "overnight", "full"), reason="Refresh AI summary after research outputs update."),
    Job("ponder_assistant", "ponder_assistant_v1.py", ("after-close", "overnight", "full"), reason="Refresh assistant/research context."),
    Job("achievements", "achievements_engine_v1.py", ("after-close", "overnight", "full"), reason="Refresh gamified progress metrics."),

    # Heavy historical refresh is intentionally not part of normal cron unless explicitly requested.
    Job("research_backfill", "research_setup_backfill.py", ("backfill",), timeout=LONG_TIMEOUT_SECONDS, reason="Optional heavy historical setup generation."),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_age_minutes(path: Path) -> Optional[float]:
    try:
        if not path.exists():
            return None
        return round((time.time() - path.stat().st_mtime) / 60, 2)
    except Exception:
        return None


def script_exists(script: str) -> bool:
    return (ROOT / script).exists()


def job_command(job: Job) -> List[str]:
    return [PYTHON, job.script]


def selected_jobs(mode: str, include_backfill: bool = False) -> List[Job]:
    out = [job for job in JOBS if mode in job.modes]
    if include_backfill and mode != "backfill":
        out.extend(job for job in JOBS if "backfill" in job.modes)
    return out


def run_job(job: Job, dry_run: bool = False) -> Dict[str, Any]:
    path = ROOT / job.script
    result: Dict[str, Any] = {
        "name": job.name,
        "script": job.script,
        "exists": path.exists(),
        "required": job.required,
        "reason": job.reason,
        "command": " ".join(job_command(job)),
        "started_at": utc_now(),
        "finished_at": None,
        "duration_seconds": 0.0,
        "returncode": None,
        "status": "pending",
        "stdout_tail": "",
        "stderr_tail": "",
    }

    if not path.exists():
        result.update({"status": "missing_required" if job.required else "missing_skipped", "finished_at": utc_now()})
        return result

    if dry_run:
        result.update({"status": "dry_run", "finished_at": utc_now()})
        return result

    started = time.time()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            job_command(job),
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=job.timeout,
            check=False,
        )
        duration = round(time.time() - started, 2)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        result.update(
            {
                "finished_at": utc_now(),
                "duration_seconds": duration,
                "returncode": proc.returncode,
                "status": "ok" if proc.returncode == 0 else "error",
                "stdout_tail": stdout[-2000:],
                "stderr_tail": stderr[-2000:],
            }
        )
        log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{job.name}.log"
        log_file.write_text(
            f"COMMAND: {' '.join(job_command(job))}\nRETURN: {proc.returncode}\nDURATION: {duration}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n"
        )
        result["log_file"] = str(log_file.relative_to(ROOT))
    except subprocess.TimeoutExpired as exc:
        result.update(
            {
                "finished_at": utc_now(),
                "duration_seconds": round(time.time() - started, 2),
                "returncode": None,
                "status": "timeout",
                "stdout_tail": str(exc.stdout or "")[-2000:],
                "stderr_tail": str(exc.stderr or "")[-2000:],
            }
        )
    except Exception as exc:
        result.update(
            {
                "finished_at": utc_now(),
                "duration_seconds": round(time.time() - started, 2),
                "returncode": None,
                "status": "exception",
                "stderr_tail": f"{type(exc).__name__}: {exc}",
            }
        )

    return result


def freshness_snapshot() -> Dict[str, Any]:
    files = {
        "market_intelligence": RESEARCH_OUT / "market_intelligence_latest.json",
        "market_regime": RESEARCH_OUT / "market_regime_filter_latest.json",
        "sell_intelligence": RESEARCH_OUT / "sell_intelligence_latest.json",
        "rotation_engine": RESEARCH_OUT / "rotation_engine_latest.json",
        "rotation_performance": RESEARCH_OUT / "rotation_performance_latest.json",
        "capital_intelligence": RESEARCH_OUT / "capital_intelligence_latest.json",
        "shadow_execution": RESEARCH_OUT / "shadow_execution_latest.json",
        "shadow_live_comparison": RESEARCH_OUT / "shadow_live_comparison_latest.json",
        "shadow_capital_allocator": RESEARCH_OUT / "shadow_capital_allocator_v2_latest.json",
        "setup_outcomes": RESEARCH_OUT / "setup_outcomes_latest.json",
        "strategy_research": RESEARCH_OUT / "shadow_strategy_research_latest.json",
        "near_miss_tracker": RESEARCH_OUT / "near_miss_tracker_latest.json",
        "system_snapshot": RESEARCH_OUT / "system_snapshot_latest.json",
        "bot_status": ROOT / "bot_status.json",
        "top_candidates": ROOT / "top_10_candidates_v2.json",
        "shadow_setups_csv": ROOT / "research_data" / "shadow_setups.csv",
        "near_miss_csv": ROOT / "research_data" / "near_miss_signals.csv",
    }
    return {
        name: {
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "age_minutes": file_age_minutes(path),
        }
        for name, path in files.items()
    }


def inspect_repo() -> Dict[str, Any]:
    job_rows = []
    for job in JOBS:
        path = ROOT / job.script
        job_rows.append({**asdict(job), "exists": path.exists(), "path": str(path.relative_to(ROOT))})
    return {
        "status": "inspect_only",
        "generated_at": utc_now(),
        "scheduler_exists": True,
        "jobs": job_rows,
        "freshness": freshness_snapshot(),
        "notes": [
            "Repo inspection can confirm scheduler files and research scripts, but cannot prove the VPS user's crontab is installed.",
            "Run `crontab -l | sed -n '/PONDER_RESEARCH_SCHEDULER_START/,/PONDER_RESEARCH_SCHEDULER_END/p'` on the VPS to verify cron installation.",
            "This scheduler is research-only and does not change live trading logic.",
        ],
    }


def run_mode(mode: str, dry_run: bool = False, include_backfill: bool = False) -> Dict[str, Any]:
    jobs = selected_jobs(mode, include_backfill=include_backfill)
    results = [run_job(job, dry_run=dry_run) for job in jobs]
    status_counts: Dict[str, int] = {}
    for result in results:
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
    output = {
        "status": "ok" if not any(r["status"] in {"error", "timeout", "exception", "missing_required"} for r in results) else "warning",
        "mode": mode,
        "dry_run": dry_run,
        "include_backfill": include_backfill,
        "generated_at": utc_now(),
        "python": PYTHON,
        "status_counts": status_counts,
        "jobs_run": results,
        "freshness": freshness_snapshot(),
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "automation_allowed": False,
            "live_trading_changed": False,
            "note": "Research scheduler only runs dashboard/research scripts. It does not import bot.py or place orders.",
        },
    }
    return output


def write_output(payload: Dict[str, Any]) -> None:
    RESEARCH_OUT.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Research-only scheduler for Ponder Invest AI.")
    parser.add_argument("--mode", choices=["inspect", "intraday", "after-close", "overnight", "full", "backfill"], default="inspect")
    parser.add_argument("--dry-run", action="store_true", help="Print planned jobs without executing them.")
    parser.add_argument("--include-backfill", action="store_true", help="Include heavy historical backfill job in addition to selected mode.")
    args = parser.parse_args(argv)

    if args.mode == "inspect":
        payload = inspect_repo()
    else:
        payload = run_mode(args.mode, dry_run=args.dry_run, include_backfill=args.include_backfill)

    write_output(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


if __name__ == "__main__":
    main()
