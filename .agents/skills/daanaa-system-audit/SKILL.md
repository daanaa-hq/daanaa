# Daanaa System Audit Skill

## Purpose

Repeat or update the Daanaa system audit using repository evidence only.

## When to use

- Inspecting architecture, workflows, data lineage, security, reliability, performance, UX, AI governance, and documentation.
- Updating the audit after repository changes.
- Comparing a new state against an older audit package.

## Read-only safety

- Do not modify application code, migrations, deployment files, env files, or infrastructure.
- Only write audit artifacts inside `docs/daanaa-system-audit/` and the skill file itself.
- Redact secrets and do not copy credentials into reports.

## Procedure

1. Record git status, branch, and commit.
2. Read the governance files and institutional state files.
3. Inventory the repo with file search and targeted source reads.
4. Trace workflows from trigger to user-visible result.
5. Classify evidence as confirmed, strong evidence, probable, or requires verification.
6. Build findings, gap registers, and remediation priorities.
7. Write source diagrams and a static dashboard.
8. Cross-check public wording against actual implementation.
9. Compare against the previous audit and note new gaps or closed gaps.

## Evidence standards

- Every important claim needs a file path, route, function, table, schema, script, test, or config reference.
- Do not infer an end-to-end connection solely from filename similarity.
- Distinguish AI-assisted work from deterministic calculation and from human approval.

## Gap classification

- Critical: immediate security, financial, legal, or major data-integrity risk.
- High: likely user-facing failure or serious trust issue.
- Medium: reliability, efficiency, maintainability, or scaling weakness.
- Low: cleanup, documentation, or nonurgent improvement.

## Diagram requirements

- Use Mermaid source files.
- Show trust boundaries, read/write direction, human approval gates, and unverified connections.
- Keep executive diagrams simple and separate from engineering detail.

## Pitch requirements

- Distinguish personal design/decision-making from AI assistance and automatic system behavior.
- Avoid exaggerating implementation maturity or business outcomes.
- Use evidence-led claims only.

## Comparison against a previous audit

- Preserve historical reports in a dated audit directory.
- Do not overwrite old audit packages.
- When comparing, identify new files, removed files, changed terminology, and newly introduced gaps.

## Completion

The audit is complete when:

- The requested report set exists.
- The diagrams and dashboard are consistent with the evidence.
- No secrets are exposed.
- Changes are limited to the audit package and this skill file.

