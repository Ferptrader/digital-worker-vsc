"""Offline CI checks for F2. Checks do not grant GxP authority."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

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

def assert_gxp_blocked(res):
    assert res["gxp_release_authorized"] is False
    assert res["harness_authoritative_gate"] == "HOLD"
    assert all(res["quality_gates"][k] == "HOLD" for k in ("G0", "G4", "G5"))
    assert res["execution"]["oq_executed"] == 0
    assert res["execution"]["harness_tests_executed"] == 0
    assert res["execution"]["oq_planned"] == 16
    assert res["execution"]["harness_tests_planned"] == 22

def main():
    if len(sys.argv) != 2:
        print("Usage: python ci_assert.py path/to/reports",file=sys.stderr)
        return 2
    reports=Path(sys.argv[1]).resolve()
    check_source()
    good = load(reports / "clean" / "verification.json")
    bad = load(reports / "negative" / "verification.json")
    for name in ("clean", "negative"):
        check_output_hashes(reports/name)
    for res in (good,bad):
        assert_gxp_blocked(res)
    assert good["source_integrity_status"] == "PASS"
    assert good["documentary_structural_status"] == "PASS"
    assert good["counts"]["checks_fail"] == 0
    assert good["counts"]["findings"] == 0
    assert good["counts"]["traces"] == 16
    assert bad["documentary_structural_status"] == "FAIL"
    assert bad["comparisons"]["export"]["status"] == "FAIL"
    assert any(x["id"] == "CMP-DIFF" for x in bad["findings"])
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
