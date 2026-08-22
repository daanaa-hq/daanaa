# Core — Production Essentials

## Canonical Files

- **`droplet_api.py`** — Flask backend serving daanaa.org (11k lines, 189 routes). Synced to droplet every deploy.
- **`overnight_pipeline.py`** — Nightly orchestrator (runs at 2am). Coordinates scoring, FTS index, missions, discovery.

## For Local Development

```bash
source ~/meritgiving/venv/bin/activate
python3 scripts/core/droplet_api.py         # Dev: single-process Flask
# or via symlink (backward compat):
python3 scripts/droplet_api.py              # Same thing
```

## Deployment

```bash
./scripts/ops/sync_droplet_api.sh           # Auto-deploys to droplet, smoke tests, auto-rollbacks on failure
```

## Architecture Notes

- **droplet_api.py** is lean (no v4_scores, no embeddings in-memory). The droplet `search.db` is the contract.
- **overnight_pipeline.py** orchestrates but doesn't run tasks itself — it kicks off scripts in `discovery/`, `scoring/`, `enrichment/`.
- Both are intentionally kept slim for maintainability (no God classes).

## Do Not Use

- `merit_api.py` (removed 2026-05-20)

**Corrected 2026-08-22:** the line above previously also listed `daanaa_api.py`
as "archived 2026-07-15" — that's wrong. `daanaa_api.py` (repo root) is the
live local-dev copy of the API, actively edited alongside `droplet_api.py`.
See CLAUDE.md's "Which backend is canonical" section.

## History

- Moved to `scripts/core/` 2026-08-12 (folder structure refactoring, Jake Van Clief model)
- **Corrected 2026-08-22** (verified via `ls -la`, not assumed): `scripts/droplet_api.py`
  is a real symlink (→ `../droplet_api.py`). `scripts/overnight_pipeline.py`
  is NOT a symlink — that compat path was never created. The only real file
  is `scripts/core/overnight_pipeline.py`; the crontab correctly references
  that full path directly, not the bare compat path.
