from pathlib import Path

p = Path("research_pipeline_v1.py")
text = p.read_text()
p.with_suffix(".py.bak_sell_intel_v1").write_text(text)

if 'run(["python3", "sell_intelligence_v1.py"])' not in text:
    text = text.replace(
        'run(["python3", "overnight_brief_v1.py"])',
        'run(["python3", "overnight_brief_v1.py"])\n    run(["python3", "sell_intelligence_v1.py"])'
    )

if '"sell_intelligence": {}' not in text:
    text = text.replace(
        '"overnight_brief": {},',
        '"overnight_brief": {},\n        "sell_intelligence": {},'
    )

if 'sell_json = Path("static/research/sell_intelligence_latest.json")' not in text:
    text = text.replace(
        'overnight_json = Path("static/research/overnight_brief_latest.json")',
        'overnight_json = Path("static/research/overnight_brief_latest.json")\n    sell_json = Path("static/research/sell_intelligence_latest.json")'
    )

    text = text.replace(
        'if optimizer_csv.exists():',
        'if sell_json.exists():\n        payload["sell_intelligence"] = json.loads(sell_json.read_text())\n\n    if optimizer_csv.exists():'
    )

p.write_text(text)
print("✅ Sell intelligence added to research pipeline")
