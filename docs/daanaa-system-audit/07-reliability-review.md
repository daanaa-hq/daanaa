# Reliability Review

## Strengths

- Search reliability has direct regression coverage.
- Claim flow has direct regression coverage.
- Principle tests catch several load-bearing invariants.
- The droplet API reopens its search database on inode change, which supports atomic replacement of search artifacts.

## Gaps

- The repo contains multiple incident notes in `LESSONS.md` about schema drift, stale deploys, and overlapping pipeline writers.
- Some batch jobs appear to be cron-driven without a clearly documented dead-letter or quarantine path in the current code snapshot.
- Several scripts suggest best-effort behavior and silent fallback rather than explicit recovery in some enrichment paths.

