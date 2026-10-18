"""Offline CI checks for F2. Checks do not grant GxP authority."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def require(condition: bool, message: str) -> None:
    """Always enforce conditions, including when Python runs with -O."""
    if not condition:
        raise ValueError(message)

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def check_source():
    mf = ROOT / "F1_SOURCE_SHA256.txt"
    seen = set()
    for line in mf.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        if not rel or rel in seen or len(expected) != 64:
            raise ValueError("Duplicated/invalid source entry")
        seen.add(rel)
        path = ROOT / rel
        if path.is_symlink() or not path.is_file() or ROOT.resolve() not in path.resolve().parents:
            raise ValueError("Unexpected source path: " + rel)
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected != observed:
            raise ValueError("Source digest mismatch: " + rel)
    if len(seen) != 8:
        raise ValueError("Unexpected source manifest cardinality")

def check_output_hashes(base: Path):
    lines = (base / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    if len(lines) != 4:
        raise ValueError("Expected four report hashes")
    seen = set()
    allowed={"verification.json","findings.csv","traceability.csv","summary.txt"}
    for row in lines:
        expected, filename = row.split("  ", 1)
        if filename not in allowed or filename in seen:
            raise ValueError("Unexpected/duplicate report: " + filename)
        seen.add(filename)
        found = hashlib.sha256((base / filename).read_bytes()).hexdigest()
        if found != expected:
            raise ValueError("Report hash mismatch: " + filename)
    if seen != allowed:
        raise ValueError("Missing output hash entry")

def assert_gxp_blocked(res: dict, label: str) -> None:
    require(res.get("gxp_release_authorized") is False,
            f"{label}: GxP release must be explicitly false")
    require(res.get("harness_authoritative_gate") == "HOLD",
            f"{label}: authoritative harness gate must be HOLD")
    gates = res.get("quality_gates", {})
    require(isinstance(gates, dict) and all(gates.get(k) == "HOLD" for k in ("G0", "G4", "G5")),
            f"{label}: G0/G4/G5 must remain HOLD")
    execution = res.get("execution", {})
    require(execution.get("oq_executed") == 0 and execution.get("harness_tests_executed") == 0,
            f"{label}: no actual OQ/HT execution is authorized")
    require(execution.get("oq_planned") == 16 and execution.get("harness_tests_planned") == 22,
            f"{label}: expected planned test counts changed")


def check_unit_test_run(reports: Path) -> None:
    """Detect empty/partial unittest discovery even if process exit is 0."""
    log = (reports / "tests.log").read_text(encoding="utf-8")
    passed = re.findall(r"(?m)^test_[A-Za-z0-9_]+ \([^\r\n]+\) \.\.\. ok$", log)
    require(len(passed) == 20, f"Expected 20 individual passing tests; got {len(passed)}")
    require(re.search(r"(?m)^Ran 20 tests in [0-9.]+s$", log) is not None,
            "Unittest summary must report exactly 20 executed tests")
    require(re.search(r"(?m)^OK$", log) is not None,
            "Unittest summary is not OK")


def check_negative_exit(reports: Path) -> None:
    raw = (reports / "negative_exit_code.txt").read_text(encoding="utf-8").strip()
    # Original workflow logs NEGATIVE_EXIT_CODE=1; local reproduction may use just 1.
    require(raw in ("1", "NEGATIVE_EXIT_CODE=1"),
            "Expected structural negative test exit code 1")


def main():
    if len(sys.argv) != 2:
        print("Usage: python ci_assert.py path/to/reports",file=sys.stderr)
        return 2
    reports=Path(sys.argv[1]).resolve()
    check_source()
    check_unit_test_run(reports)
    check_negative_exit(reports)
    good = load(reports / "clean" / "verification.json")
    bad = load(reports / "negative" / "verification.json")
    for name in ("clean", "negative"):
        check_output_hashes(reports/name)
    for label, res in (("clean", good), ("negative", bad)):
        assert_gxp_blocked(res, label)
    require(good.get("source_integrity_status") == "PASS", "Clean fixture integrity failure")
    require(good.get("documentary_structural_status") == "PASS", "Clean structural verification failure")
    counts = good.get("counts", {})
    require(counts.get("checks_fail") == 0 and counts.get("findings") == 0 and counts.get("traces") == 16,
            "Clean verification findings or trace count changed")
    require(bad.get("documentary_structural_status") == "FAIL", "Negative fixture falsely marked PASS")
    comparisons = bad.get("comparisons", {})
    require(isinstance(comparisons, dict) and comparisons.get("export", {}).get("status") == "FAIL",
            "Negative export comparison not marked FAIL")
    require(any(x.get("id") == "CMP-DIFF" for x in bad.get("findings", [])),
            "Negative export tampering is not reported as CMP-DIFF")
    summary = (
      "# JARVIS HYB F2 — Inspecao tecnica do CI (SIM-EMS)\n\n"
      "- 20 testes unitarios: verificar `tests.log`\n"
      "- Verificacao estrutural: **PASS**\n"
      "- Teste negativo de exportacao alterada: **FAIL esperado, detectado**\n"
      "- Digest de 8 fontes e 8 arquivos de saida: **consistente**\n"
      "- G0/G4/G5: **HOLD** (sem alteracao)\n"
      "- OQ: 0/16; HT: 0/22; aprovacao GxP: **nao autorizada**\n\n"
      "> Aprovacao tecnica CI != conformidade ou liberacao GxP.\n"
    )
    (reports/"ci_summary.md").write_text(summary,encoding="utf-8")
    print("F2: LOCAL CI ASSERTIONS PASS — GxP release denied / G0-G4-G5 HOLD")
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except (AssertionError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("F2: CI ASSERTIONS FAILED:",repr(exc),file=sys.stderr)
        sys.exit(1)
