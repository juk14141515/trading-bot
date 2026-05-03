import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_FILE = Path(__file__).with_name("shadow_ideas.json")

WINDOWS = {"30m": timedelta(minutes=30), "1h": timedelta(hours=1), "1d": timedelta(days=1)}

@dataclass
class EvalStats:
    pending_loaded: int = 0
    evaluated_now: int = 0
    skipped_too_new: int = 0
    errors: int = 0


def load_ideas() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text())


def save_ideas(ideas: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(ideas, indent=2))


def _safe_num(v, default=None):
    try:
        return float(v)
    except Exception:
        return default


def evaluate_shadow_ideas(now: datetime | None = None) -> EvalStats:
    now = now or datetime.now(timezone.utc)
    ideas = load_ideas()
    stats = EvalStats(pending_loaded=sum(1 for i in ideas if i.get("status") != "evaluated"))

    for idea in ideas:
        try:
            _normalize_idea(idea)
            if idea["status"] == "evaluated":
                continue
            created_at = datetime.fromisoformat(idea["created_at"])
            changed = False
            for w_name, w_delta in WINDOWS.items():
                window = idea["evaluations"].setdefault(w_name, {"status": "pending"})
                if window.get("status") == "evaluated":
                    continue
                if now - created_at < w_delta:
                    stats.skipped_too_new += 1
                    continue
                outcome = _evaluate_window(idea)
                window.update(outcome)
                window["window"] = w_name
                window["evaluated_at"] = now.isoformat()
                window["status"] = "evaluated"
                changed = True
                stats.evaluated_now += 1
            if all(v.get("status") == "evaluated" for v in idea["evaluations"].values()):
                idea["status"] = "evaluated"
            if changed:
                last = list(idea["evaluations"].values())[-1]
                idea["result"] = last.get("result")
                idea["alpha"] = last.get("alpha")
                idea["outcome"] = last.get("outcome")
        except Exception:
            stats.errors += 1
    save_ideas(ideas)
    return stats


def _evaluate_window(idea: dict) -> dict:
    t = idea.get("type")
    if t == "rotation":
        ef = _safe_num(idea.get("entry_from_price")); et = _safe_num(idea.get("entry_to_price"))
        cf = _safe_num(idea.get("latest_from_price"), ef); ct = _safe_num(idea.get("latest_to_price"), et)
        if not ef or not et:
            return {"result": "Not evaluated yet", "alpha": None, "outcome": "unresolved"}
        alpha = ((ct-et)/et)-((cf-ef)/ef)
    else:
        e = _safe_num(idea.get("entry_price")); c = _safe_num(idea.get("latest_price"), e)
        if not e:
            return {"result": "Not evaluated yet", "alpha": None, "outcome": "unresolved"}
        alpha = (e-c)/e if idea.get("action","").lower().startswith(("sell","trim")) else (c-e)/e
    if alpha > 0.005: outcome = "helped"
    elif alpha < -0.005: outcome = "hurt"
    else: outcome = "neutral"
    return {"alpha": round(alpha,6), "result": outcome.title(), "outcome": outcome}


def _normalize_idea(idea: dict) -> None:
    idea.setdefault("id", f"idea-{int(datetime.now().timestamp())}")
    idea.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    idea.setdefault("type", "rotation")
    idea.setdefault("confidence", "Low")
    idea.setdefault("action", "Watch")
    idea.setdefault("reason", "Research-only")
    idea.setdefault("status", "pending")
    idea.setdefault("evaluations", {})
    idea.setdefault("result", "Pending")
    idea.setdefault("alpha", None)
    idea.setdefault("outcome", "unresolved")


def summarize_learning() -> dict:
    ideas = load_ideas()
    evaluated = [i for i in ideas if i.get("status") == "evaluated"]
    def c(o): return sum(1 for i in evaluated if i.get("outcome") == o)
    alphas = [i.get("alpha") for i in evaluated if isinstance(i.get("alpha"), (int,float))]
    return {
        "total": len(ideas), "evaluated": len(evaluated), "pending": len(ideas)-len(evaluated),
        "helped": c("helped"), "hurt": c("hurt"), "neutral": c("neutral"),
        "win_rate": round((c("helped")/len(evaluated))*100,2) if evaluated else None,
        "avg_alpha": round(sum(alphas)/len(alphas),6) if alphas else None,
    }

if __name__ == '__main__':
    stats = evaluate_shadow_ideas()
    print(f"pending loaded: {stats.pending_loaded}")
    print(f"evaluated now: {stats.evaluated_now}")
    print(f"skipped because too new: {stats.skipped_too_new}")
    print(f"errors: {stats.errors}")
    print(f"output file updated: {DATA_FILE}")
