# Daanaa System Audit

This directory is a read-only audit package for the current Daanaa repository state.

## What is included

- Executive, architecture, workflow, data, security, reliability, performance, UX, AI-governance, and testing reviews.
- Structured CSV evidence extracts.
- Mermaid source diagrams for major workflows and trust boundaries.
- A static dashboard for screen-sharing.
- Pitch and interview materials based only on repository evidence.
- A reusable Codex skill for repeating the audit later.

## Evidence standard

- `Confirmed` means directly supported by repository code or repo-owned documentation.
- `Strong evidence` means multiple source files strongly imply the behavior, but one link in the chain is still indirect.
- `Probable` means the repo points in that direction, but the connection needs runtime or broader validation.
- `Requires verification` means the repo does not yet prove the behavior.

## Reading order

1. `00-executive-summary.md`
2. `01-system-inventory.md`
3. `02-architecture-overview.md`
4. `04-workflow-catalog.md`
5. `06-security-review.md`
6. `10-ai-governance-review.md`
7. `13-prioritized-remediation-plan.md`

## Dashboard

Open `dashboard/index.html` in a browser after starting a local static server with `serve-report.sh`.

