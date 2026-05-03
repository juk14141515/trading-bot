from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "bot.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"bot.py.bak_fix_learning_indent_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

# Fix wrongly indented skip-buy blocks
txt = txt.replace(
'''        log_learning_event("LEARNING_SHADOW_SKIP_BUY", symbol=symbol, score=final_score if "final_score" in locals() else "", reason="skip buy")
            # LEARNING_SHADOW_SKIP_BUY
            log(f"SKIP BUY | {symbol} | invalid position size")
''',
'''        log_learning_event("LEARNING_SHADOW_SKIP_BUY", symbol=symbol, score=score, reason="invalid position size")
        # LEARNING_SHADOW_SKIP_BUY
        log(f"SKIP BUY | {symbol} | invalid position size")
'''
)

txt = txt.replace(
'''        log_learning_event("LEARNING_SHADOW_SKIP_BUY", symbol=symbol, score=final_score if "final_score" in locals() else "", reason="skip buy")
            # LEARNING_SHADOW_SKIP_BUY
            log(f"SKIP BUY | {symbol} | would exceed max deployed")
''',
'''        log_learning_event("LEARNING_SHADOW_SKIP_BUY", symbol=symbol, score=score, reason="would exceed max deployed")
        # LEARNING_SHADOW_SKIP_BUY
        log(f"SKIP BUY | {symbol} | would exceed max deployed")
'''
)

# Fix wrongly indented buy decision comment
txt = txt.replace(
'''            log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason="candidate selected")
            # LEARNING_SHADOW_BUY_DECISION
            log(f"BUY DECISION | {symbol}''',
'''            log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason="candidate selected")
            # LEARNING_SHADOW_BUY_DECISION
            log(f"BUY DECISION | {symbol}'''
)

txt = txt.replace(
'''            log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason="candidate selected")
                # LEARNING_SHADOW_BUY_DECISION
                log(f"BUY DECISION | {symbol}''',
'''            log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason="candidate selected")
            # LEARNING_SHADOW_BUY_DECISION
            log(f"BUY DECISION | {symbol}'''
)

FILE.write_text(txt)
print("DONE: learning shadow indentation fixed")
print("NEXT:")
print("python3 -m py_compile bot.py")
