# AENV-REAL-002 — Operational access and segregated AWS validation

Status: **PREPARED / NOT EXECUTED ON AWS / NOT QUALIFIED** (2026-10-15).

## Original Atlas site

- Original site ID: `appgprj_6acc132b91bc8191a7b0d46ec3004159`.
- No alternative site created; the principal private map was not mutated.
- `labs/atlas_site_readonly/probe.py` performs a GET for public reachability with no credentials, cookie or private writes.
- **A successful public probe does not test the map-navigation issue.** To close that defect an authorized executor must obtain original source revision, make backup, patch navigation to avoid reset, run in-browser regression on QA project, publish to **same site**, then verify project `principal` revision and 40 nodes, 32 edges, 1 risk, 4 documents unchanged. If unavailable, keep defect OPEN.

## AWS — minimum authorized independent validation

- Target existing C005 gate `labs/jasap_c005/aws_preflight.py` in sandbox branch `sandbox/jarvis-aenv-real-component-tests-20261015`.
- Access to real AWS requires a pre-existing permissioned role in **anchor** account and a separate **witness** account, actual account IDs, table, bucket and region. Do not guess any of these.
- Command (execute only in an authorized existing AWS session):
  `python aws_preflight.py --table <ACTUAL_TABLE> --bucket <ACTUAL_WORM_BUCKET> --region <ACTUAL_REGION> --anchor-account <ACTUAL_ANCHOR_ACCOUNT> --witness-account <ACTUAL_WITNESS_ACCOUNT>`
- Verify STS principal, ownership, DynamoDB PITR and delete protection, S3 Object Lock COMPLIANCE default retention, versioning, policy, public access block and ability to enumerate witness history.
- Separate positive and negative IAM authorization tests and independent administrator review still required, along with replay/concurrency/network failure/reconciliation tests and authentic immutable evidence.
- No cloud resources, keys, policies, roles, or credentials were created or modified in this preparatory work.
- A successful read-only preflight alone cannot close critical risks IA-02 and IDEMP-01 or grant GxP release.

Baseline JV8-BL-001 remains unchanged; follow ISO/GAMP/CSV human review before promotion.
