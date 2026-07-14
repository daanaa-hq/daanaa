# Institutional Memory Review

Date: 2026-07-13

## Current Memory Stores

`institution/SUCCESSION.md` already identifies seven stores:

1. Git repository
2. `institution/`
3. AI session memory
4. Workflow tool state
5. Vector cache
6. Database backups
7. Droplet deployment target

## Strengths

- Authority order is explicit.
- Decision and lesson logs are detailed and practical.
- Current state, risk register, succession plan, board/founder records, reviews, and task records exist.
- Backup script has been updated to fail loudly.
- The institution directory is tracked as constitutional memory.

## Gaps

- AI session memory migration remains documented as urgent but not verified complete.
- `.gstack/` and `.superpowers/` contain workflow history that may include decisions not backported to `DECISIONS.md` or `LESSONS.md`.
- Historical docs need status labels to prevent accidental revival.
- Provider-console authority remains outside repo evidence.

## Recommendation

Run a memory backport sprint:

- Identify high-value hidden memory records.
- Backport durable decisions to `DECISIONS.md`.
- Backport failure rules to `LESSONS.md`.
- Preserve historical records under `institution/historical/` only after classification.
- Avoid dumping raw hidden state into canonical memory without review.

