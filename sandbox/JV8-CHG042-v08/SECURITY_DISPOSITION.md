# JV8 CHG-042 v0.8 — security adapter evaluation record

Date: 2026-10-09, America/Sao_Paulo.
Status: **CANDIDATE / HOLD / NOT QUALIFIED / NOT PROMOTED**.

This is a documentation-only sandbox branch. This repository is **not confirmed** as the authoritative JARVIS V8.1 runtime. No executable source or active baseline was modified, deployed, released or qualified.

## Change scope

Separate v0.8 security adapter for three remaining risk cases, preserving the v0.7 source as a legacy synthetic fixture:

- **E11**: signed Ed25519 identity grants (issuer, audience, public key, time limits, roles, tenant/project and revocation callback) through `ControlledBridge`.
- **E21**: two separately signed reviewer/Quality role grants, plus a distinct submitter, through `ControlledRegistry`. This is **simulation only**, not a Part 11/electronic GxP signature.
- **E22**: signed report attestation with pinned public key, report SHA-256, scope, run ID, time window and anti-replay. No production attestor is connected.

## Measured results

- Existing v0.7 regression **119/119 PASS**.
- New synthetic security adapter checks **50/50 PASS**.
- Replayed frozen legacy adversarial campaign **39/42 PASS**, with **E11, E21, E22 still FAIL on legacy APIs**. Never claim 42/42.
- Extracted v0.8 archive: **169/169 internal regression + adapter checks PASS**.

## Immutable candidate information

- Candidate ZIP SHA-256: `24e8304b9a02e1dac854c6db2f1a60dda59d4b87ea16447a626e8dffa9c8999b`
- v0.8 evaluation report SHA-256: `2a28a1e655e9e097a97ad0c27c5b0a76fb84724d65a65ab693b52bd318efbeb0`
- Original v0.7 candidate SHA-256: `9bbafa83566326f624179cbd1596b36869845ec8eb260743d3c4416789f312b3`
- Frozen evaluator SHA-256: `f81197218b856e472353edad8d09a3926304ae82a44afed40104e36f0345bec2`

The candidate and report are archived under the ChatGPT Library:
`/JARVIS/V8.1/LifecycleControl/CHG042_Candidate/`

## Mandatory gates

Confirm the real authoritative JARVIS runtime, configure enterprise IdP and revocation, integrate an independent signing/attestation service with protected key custody, isolate the unsafe legacy API from the runtime, conduct an independent blind evaluation, and obtain formal Quality authorization and rollback approval before any promotion.

**No shared learning, no production approval, no automatic GxP signature or release.** Baseline JV8-BL-001 V8.1 Rev03.1 ACTIVE, R-01 to R-05 and Human/Quality Gate remain unchanged.
