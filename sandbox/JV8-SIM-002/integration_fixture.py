"""SIMULACAO JV8-SIM-002. Sem uso GxP. Fixture sintetica autorizada.
URS: https://drive.google.com/file/d/1_w_oMnIg8HTd75c4mk-KKCD2g2YudtpV/view?usp=drivesdk
DEC-001: https://app.notion.com/p/3ed3d584e83c81fc8cd8cf6ba79e0467?pvs=204
CHG-001 / RISK-001 / URS-001..003. Avaliacao interna, nao independente.
"""
import math
import json

def evaluate(value, corrected=True):
    # URS-003
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("invalid temperature")
    # URS-001, URS-002; CHG-001 altera somente a fronteira
    alarm = value >= 8.0 if corrected else value > 8.0
    return "ALARME" if alarm else "NORMAL"

CASES = [
    ("T01", "URS-002", 7.9, "NORMAL"),
    ("T02", "URS-001", 8.0, "ALARME"),
    ("T03", "URS-001", 8.1, "ALARME"),
    ("T04", "URS-003", float("nan"), "INVALID"),
    ("T05", "URS-003", float("inf"), "INVALID"),
    ("T06", "URS-003", "8.0", "INVALID"),
    ("T07", "URS-003", True, "INVALID"),
]

def run(corrected):
    rows = []
    for test_id, requirement, value, expected in CASES:
        try:
            actual = evaluate(value, corrected)
        except ValueError:
            actual = "INVALID"
        rows.append(dict(test=test_id, requirement=requirement, risk="RISK-001" if test_id=="T02" else "SIM-input", expected=expected, actual=actual, status="PASS" if actual==expected else "FAIL"))
    return rows

if __name__ == "__main__":
    before, after = run(False), run(True)
    print(json.dumps({"project":"JV8-SIM-002", "simulation":True, "before":before, "after":after}, indent=2))
    assert [r["test"] for r in before if r["status"]=="FAIL"] == ["T02"], "unexpected baseline"
    assert all(r["status"]=="PASS" for r in after), "corrected version failed"
