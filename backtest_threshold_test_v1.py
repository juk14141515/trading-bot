import pandas as pd
import subprocess

thresholds = [65, 70, 75, 80, 85]

for t in thresholds:
    print("\n====================")
    print(f"Testing threshold {t}")
    print("====================")

    text = open("backtest_sim_v1.py").read()
    text = text.replace(
        next(line for line in text.splitlines() if line.startswith("BUY_THRESHOLD =")),
        f"BUY_THRESHOLD = {t}"
    )
    open("backtest_sim_v1_tmp.py", "w").write(text)

    subprocess.run(["python3", "backtest_sim_v1_tmp.py"])
