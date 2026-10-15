# JARVIS C005 — operational gates (laboratory only)

**2026-10-15 | LAB ONLY / HOLD / NOT QUALIFIED**

The actual Python sources from C004 and a new read-only AWS account preflight are now versioned under `labs/jasap_c005/` in this branch. Baseline JV8-BL-001 / JARVIS V8.1 Rev03.1 remains untouched.

## Verification
- 53/53 local Python tests PASS on 2026-10-15; 48 inherited C004 tests and 5 new AWS preflight contract tests.
- CI source: `.github/workflows/jarvis-c005-isolated-assurance.yml`; workflow has been committed, but remote CI execution has **not** been confirmed.
- C005 ZIP SHA-256: `bf2d2dda0463c5f89b16a29a174f6e6f1de710efc166a0baa2413d7627dbe17c`, delivered via conversation.
- To execute locally: `cd labs/jasap_c005 && python -m pip install -r requirements-lab.txt && PYTHONPATH=. python -m unittest discover -s tests -v`.
- AWS preflight: `python aws_preflight.py --table TABLE --bucket BUCKET --region us-east-1 --anchor-account 111111111111 --witness-account 222222222222` with **real, authorized, read-only credentials**.
- AWS preflight was **NOT run against actual AWS** because authorized accounts/credentials were unavailable. Even a passing preflight reports `INFRASTRUCTURE_PRESENT_NOT_QUALIFIED`.

## Risks still open
- **IA-02 OPEN CRITICAL:** AWS IAM actual deny tests, separate administrators, key revocation/rotation, authoritative dispatcher identity and proven cross-account boundaries absent.
- **IDEMP-01 OPEN CRITICAL:** E2E side-effect fencing/reconciliation, real DynamoDB conditional reservation, Object Lock version retention test, multi-host concurrency/recovery and genuine immutable witness evidence absent.
- Actual MCP/A2A, JARVIS operational runtime and GxP release not performed.
- Existing mock tests and static CloudFormation are not sufficient to close either risk.

## Deployment decision
No automatic deploy. Do not merge to main or release. Cost, account ownership, IAM least privilege, immutable retention period, and separate Quality/security approval must be resolved before any cloud provisioning.

For authoritative security evidence, see `docs/JARVIS_C004_SECURITY_HARDENING_20261015.md` and `labs/jasap_c005/tests/`.
