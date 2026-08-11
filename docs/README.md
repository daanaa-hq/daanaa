# Daanaa Documentation Hub

This directory contains active product, engineering, operations, research, governance-supporting, and historical documentation. The filename alone is not an authority signal.

## Read first

For repository navigation, read [REPO_MAP.md](../REPO_MAP.md). For binding operating rules, read [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md), [STEWARDSHIP.md](../STEWARDSHIP.md), [PRIVACY-INVARIANTS.md](../PRIVACY-INVARIANTS.md), [governance/DECISIONS.md](../governance/DECISIONS.md), and [governance/LESSONS.md](../governance/LESSONS.md).

For institutional authority, use [institution/README.md](../institution/README.md) and its authority order. For governance decisions and reviews, use [governance/](../governance/). Do not treat a planning document as evidence that its proposal is implemented.

## Canonical documentation paths

| Question | Canonical starting point | Status rule |
|---|---|---|
| What is Daanaa and how should it be built? | [PRODUCT.md](../PRODUCT.md), [DESIGN.md](../DESIGN.md), [STEWARDSHIP.md](../STEWARDSHIP.md) | Binding or durable guidance; implementation must be checked separately. |
| Where is the active architecture? | [REPO_MAP.md](../REPO_MAP.md), [docs/architecture/](architecture/) | Prefer current code and tests over diagrams. |
| What is the current financial-context methodology? | [METHODOLOGY_V6_INFERENCE.md](METHODOLOGY_V6_INFERENCE.md), [scripts/daanaa_scorer.py](../scripts/daanaa_scorer.py) | v6 is current only where code and published output agree. |
| What has been decided? | [governance/DECISIONS.md](../governance/DECISIONS.md), [governance/DECISIONS.md](../governance/DECISIONS.md) | Decisions do not prove deployment. |
| What is ready to operate? | [operations/](operations/), [DEPLOYMENT.md](../DEPLOYMENT.md), [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Verify against the target environment before use. |
| What was audited? | [audit/](audit/), [daanaa-system-audit/](daanaa-system-audit/) | Preserve evidence and uncertainty labels. |

## Existing documentation areas

- architecture/, methodology/, security/, and legal/: technical or policy reference material.
- operations/, tracking/, and pilot/: operational work and bounded initiatives.
- projects/, outreach/, and partnerships/: project and relationship material.
- audit/, daanaa-system-audit/, reviews/, and superpowers/: review, audit, and agent-work records.
- The remaining flat files are legacy, active, or ambiguous. Do not move or delete them solely based on filename.

## Accuracy rules

1. A document may describe a proposal, an observation, or an implemented behavior; label which one it is.
2. Confirm implementation in code, tests, configuration, or deployment evidence before calling it operational.
3. Preserve dated and historical records; archive or move them only with link and reference checks.
4. Prefer one canonical document per decision or operating procedure. Link duplicates to the canonical source rather than silently maintaining competing copies.
5. Update this hub and REPO_MAP.md when a canonical path changes.

## Consolidation status

The documentation tree is being consolidated incrementally. This hub is the first navigation layer. Physical relocation of ambiguous documents is deferred until references, authority, and current implementation status are verified.
