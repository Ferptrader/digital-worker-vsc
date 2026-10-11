# JARVIS C001 — Adversarial finding IDEMP-01

Date: 2026-10-11
Status: **CONFIRMED FAIL / OPEN — CRITICAL / HOLD**

## Observed evidence
- GitHub Actions run: https://github.com/Ferptrader/digital-worker-vsc/actions/runs/38149258856
- Tested commit: 43a18b28bf9909929cedaa42babd21afb373b7ec
- Test: tests/test_known_open_risk_db_delete.py::KnownOpenRisk::test_deleted_sqlite_reservation_allows_reuse
- Synthetic test result: deletion of local SQLite nonce reservation database permitted nonce reuse after database recreation.
- CI job SUCCESS means the regression *confirmed the known weakness*. It is NOT security PASS.

## Impact
In the candidate gateway, SQLite is not an independent, tamper-resistant replay or side-effect anchor. An actor able to delete/recreate the DB can reset nonce memory. This does not establish exploitability in a deployed runtime: the candidate is not deployed and no authorized dispatcher is linked.

## Disposition
- IDEMP-01: **OPEN — CRITICAL**; fail-closed production gate remains HOLD.
- IA-02: OPEN — CRITICAL, separate authorization integrity issue; no automatic closure.
- INTEGRATION-006: NOT DETERMINED / HOLD.
- No merge, release, deployment or qualification claim.

## Required remediation evidence
Independent IAM and immutable witness; externally durable reservation and conditional transitions; adversarial deletion/replay/fencing tests including infrastructure fault injection; authenticated E2E trace and human/Quality review.
