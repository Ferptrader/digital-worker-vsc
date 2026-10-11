# Independent Trust Anchor — Control Plane C001 (design only)

Status: SPECIFIED / NOT IMPLEMENTED / NOT QUALIFIED.

## Goal
Prevent replay, forged authorization, lost reservations, and non-idempotent external side effects in a multi-worker JARVIS dispatcher.

## Minimum controls before activation
1. Independent IAM principal and storage administration, not sharing write/delete rights with agent runtime.
2. Durable conditional reservation keyed by authenticated tenant, operation and immutable request identifier.
3. Record content digest, initiator identity, authorization/policy version, intent, state transition and immutable witness.
4. Atomic conditional transitions and fencing tokens for stale writers; reject ambiguous/unknown effects pending reconciliation.
5. Tamper-evident write-once archival with governed retention, recovery tests and reproducible evidence checks.
6. Fail closed on witness outage or divergence; never infer PASS from an untrusted client field.
7. Include independent penetration/adversarial tests of DB deletion, replay after restart, concurrent duplicate requests, log forgery, stale writers, provider timeouts and cross-tenant access.
8. Verify key rotation/revocation, incident response, audit export, backup restoration and disaster recovery targets.
9. Review approval by designated human/Quality authority, only after traceable IQ/OQ/PQ or proportional CSA assurance.

## Acceptance evidence
- Actual IAM permissions and deny cases
- Conditional write/reconciliation trace IDs
- Immutable retention controls and independent witness records
- Failover/fencing and negative regression outputs
- Full authenticated request → worker → response E2E trace
- Approved change record and human/Quality sign-off

SQLiteReplayGuard is a single-host proof of concept only; deletion or replacement of its database may permit repeated nonces. This specification does not close IA-02, IDEMP-01, or INTEGRATION-006.

No cloud resources are provisioned by this document.
