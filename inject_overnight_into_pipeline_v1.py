from pathlib import Path

p = Path("research_pipeline_v1.py")
text = p.read_text()
p.with_suffix(".py.bak_overnight_v1").write_text(text)

if 'run(["python3", "overnight_brief_v1.py"])' not in text:
    text = text.replace(
        'run(["python3", "market_scanner_v2.py"])',
        'run(["python3", "market_scanner_v2.py"])\n    run(["python3", "overnight_brief_v1.py"])'
    )

if '"overnight_brief": {}' not in text:
    text = text.replace(
        '"optimizer_top": [],',
        '"optimizer_top": [],\n        "overnight_brief": {},'
    )

if 'overnight_json = Path("static/research/overnight_brief_latest.json")' not in text:
    text = text.replace(
        'best_json = Path("best_strategy_config_v2.json")',
        'best_json = Path("best_strategy_config_v2.json")\n    overnight_json = Path("static/research/overnight_brief_latest.json")'
    )

    text = text.replace(
        'if optimizer_csv.exists():',
        'if overnight_json.exists():\n        payload["overnight_brief"] = json.loads(overnight_json.read_text())\n\n    if optimizer_csv.exists():'
    )

p.write_text(text)
print("✅ Overnight brief added to research pipeline")
