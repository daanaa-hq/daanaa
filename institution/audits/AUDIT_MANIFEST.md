# Daanaa Repository-Wide Constitutional Audit Manifest

Started: 2026-07-13  
Continued: 2026-07-14  
Mode: Stewardship + Research + Documentation  
Write scope: documentation and audit artifacts only  
Production deployment: none  

## Purpose

This audit reviews Daanaa as an emerging institution, not merely as a codebase. It records the current evidence, conflicts, strengths, risks, and founder decisions needed before public founding documents are treated as final.

## Authority Used

Current authority order from `institution/AUTHORITY.md`:

1. `institution/PURPOSE.md`
2. `institution/COVENANT.md`
3. `institution/CONSTITUTION.md`
4. `STEWARDSHIP.md` and `institution/STEWARDSHIP.md`
5. `institution/GOVERNANCE.md`
6. Operating policies and invariants
7. Evidence snapshots and implementation records
8. Current tasks, reviews, and briefs
9. Task instructions
10. Agent implementation choices

Charter status: `institution/DAANAA-CHARTER.md` states adopted v1.0 and published at `daanaa.org/charter` on 2026-07-13. This audit treats it as a binding public promise, while still reviewing whether every promise is fully controlled.

## Scope Summary

Reviewed current governing documents, institutional library, public charter, privacy invariants, vendor policy, frontend public pages, backend API surfaces, droplet API surfaces, tests, backup script, visibility/export pipeline, and representative historical/planning documents.

Refined source inventory after excluding dependency/vendor/reference/runtime/generated paths: 3,513 paths.

Major active subsystem counts:

| Path | Count |
|---|---:|
| `visibility/` | 1,397 |
| `scripts/` | 539 |
| `frontend/` | 492 |
| `docs/` | 239 |
| `tests/` | 97 |
| `institution/` | 84 |
| `migrations/` | 7 |
| `internal/` | 5 |
| `governance/` | 1 |
| `api/` | 1 |

## Excluded Or Minimized Paths

These were inventoried by existence but not reviewed file-by-file:

- `venv/`: generated dependency environment.
- `node_modules/`, `frontend/node_modules/`: generated dependencies.
- `data/`: large datasets, SQLite databases, source data, caches, and backups.
- `frontend/dist/`, `dist/`, `precompute_output/`, `precompute_archive/`, `.deploy_scratch/`: generated build/deploy artifacts.
- `logs/`, `backups/`, `.backups/`, `.pytest_cache/`, `__pycache__/`: runtime/cache artifacts.
- `archive/`: historical code retained for reference.
- `merit-platform/`, `nonprofit-explorer/`: large reference/vendor-style trees, not treated as active Daanaa source.

Hidden state reviewed at inventory/representative level:

- `.claude/`
- `.gstack/`
- `.superpowers/`
- `.wrangler/`

## Commands And Checks Executed

- `git status --short`
- `rg --files` inventory with explicit exclusions
- Read canonical documents and representative code/tests with `sed` and `rg`
- `bash scripts/privacy_check.sh` -> pass
- `bash -n scripts/ops/daanaa_backup.sh` -> pass
- `./venv/bin/python3 -m pytest tests/test_search_reliability.py -q` -> pass
- `./venv/bin/python3 -m pytest tests/test_privacy_controls.py tests/test_concierge_confirm.py tests/test_no_public_donation_fields.py -q` -> 21 passed, 2 skipped, 6 failed

Failure summary: the concierge confirm tests fail because `_write_claimed_fields_to_registry` expects `org_claims.donate_url` while the test fixture lacks that column. This is recorded as implementation alignment finding F-006.

## Documents Created In This Packet

- `institution/audits/REPOSITORY_INVENTORY.md`
- `institution/audits/CONSTITUTIONAL_AUDIT.md`
- `institution/audits/MISSION_ALIGNMENT.md`
- `institution/audits/CHARTER_ALIGNMENT.md`
- `institution/audits/CONSTITUTIONAL_GAPS.md`
- `institution/audits/STEWARDSHIP_SCORECARD.md`
- `institution/audits/INFORMATION_PROVENANCE_REVIEW.md`
- `institution/audits/AI_GOVERNANCE_REVIEW.md`
- `institution/audits/CAPACITY_TRANSFER_REVIEW.md`
- `institution/audits/INSTITUTIONAL_MEMORY_REVIEW.md`
- `institution/audits/SUCCESSION_AND_RESILIENCE_REVIEW.md`
- `institution/audits/TECHNICAL_DEBT_BY_MISSION_IMPACT.md`
- `institution/audits/OPEN_FOUNDER_DECISIONS.md`
- `institution/audits/STRENGTHS_WORTH_PRESERVING.md`
- `institution/audits/IMPLEMENTATION_ALIGNMENT_MATRIX.md`
- `institution/publication-drafts/THE_DAANAA_VISION_v0.1.md`
- `institution/publication-drafts/DAANAA_STEWARDSHIP_CONSTITUTION_v0.1.md`
- `institution/publication-drafts/DAANAA_CHARTER_REVIEW.md`
- `institution/publication-drafts/DAANAA_RESEARCH_AGENDA_v0.1.md`
- `institution/publication-drafts/PUBLICATION_AND_SLIDE_LIBRARY_PLAN.md`

## Self-Critique Pass

After drafting, the packet was reviewed against the requested perspectives: small nonprofit executive director, donor, volunteer, privacy advocate, nonprofit attorney, AI governance researcher, engineer, future successor, skeptical public-interest journalist, mission-aligned investor, and international adapter.

Revisions made from that critique:

- Public drafts were kept as staged drafts rather than final public documents.
- Absolute Charter language was not adopted blindly; unsupported phrases are isolated in the Charter review.
- Present implementation, adopted principle, research hypothesis, and future aspiration are separated.
- Donation-boundary language was strengthened without claiming Daanaa never has donation-adjacent surfaces.
- AI empathy language was tied to disclosure, sources, uncertainty, correction, and human accountability.
- Free-platform language was flagged for founder decision instead of rewritten as if resolved.
- Firewall and quarterly-audit claims were treated as not yet publishable until controls are demonstrated.
- International adaptation language was limited to principles and explicitly rejects blind replication.

## Confidence

Overall confidence: medium-high.

High confidence for repository-local facts, governing document status, visible code/test evidence, and local command results. Medium confidence for production parity because no deployment or live provider-console verification occurred. Low confidence for billing, GitHub admin resilience, offsite backup freshness, and third-party account ownership because those facts are not fully visible from the repository.

