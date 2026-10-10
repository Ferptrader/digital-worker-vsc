# JARVIS JV8-REA-001 — Codex REA MCP integration handoff

Date: 2026-10-10  
**CANDIDATE / HOLD / MCP NOT VERIFIED / NOT PROMOTED**

## Safety scope

- Active JARVIS baseline `JV8-BL-001 — V8.1 Rev03.1 ACTIVE` is unchanged.
- This branch is **not** established as the authoritative JARVIS runtime.
- Do not access client GxP applications, production data or third-party code without authorization.
- Never print `OPENAI_API_KEY`; an OpenAI API key is not a prerequisite to REA MCP registration.
- No installation, deployment, promotion, configuration modification, or MCP registration has been performed through this record.

## Verified sources

REA upstream: https://github.com/morluto/rea  
Official installation and readiness: https://github.com/morluto/rea/blob/main/docs/installation.md  
Codex Cloud architecture: https://help.openai.com/pt-br/articles/20001545-using-codex-cloud

REA uses a **local stdio MCP server**. Codex CLI/IDE and Codex Cloud must be distinguished. Registration in a local Codex profile does not prove availability in a Cloud task.

## Run these diagnostics in the **actual Codex worker**, not in ChatGPT

1. Identify execution target: `Codex CLI/IDE local` or `Codex Cloud`, host OS and project/repository.
2. Read-only checks: `node --version`, `npm --version`, `codex --version` (only if CLI exists), `codex mcp list` (only if supported). REA requires Node.js 22.19+, 24.11+ or 26+.
3. If `rea` CLI is already installed: `rea doctor --client codex --json`. Review sanitized diagnostics. It checks host/registration but **not** an active tool call.
4. If MCP is absent: review `npm view rea-agents dist-tags.latest` and obtain an **unaltered plan**, with a compatible Node/npm environment, using `npx -y rea-agents@latest setup --client codex --dry-run --json`. This command may download package code; use only where approved.
5. **STOP** if the plan changes configuration or installs software: show the exact diff, affected paths and rollback plan for authorization. Do not automatically use `--yes`, upgrade Node or modify user-level configuration.
6. After an approved setup/restart, check the **active session's** MCP tool list and invoke a REA tool on a locally generated synthetic JavaScript fixture. Capture sanitized evidence and exit/status without displaying source secrets.
7. A fallback such as `rea analyze-javascript-application /absolute/path/to/synthetic-app --json` demonstrates CLI analysis only, **not** MCP connectivity.

## Release criteria

- `CONFIG_PASS`: compatible runtime plus enabled MCP registration (insufficient for operational).
- `MCP_PASS`: real REA tool invocation through active Codex MCP connection to intended runtime and synthetic target; verified output/evidence.
- `SCOPE_PASS`: no baseline/production/shared learning changes, no credentials exposed.
- Until all relevant checks pass: `HOLD / NOT CONNECTED`.

This candidate handoff is documentation, not proof of installation or connection.
