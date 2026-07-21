# Dead code archived 2026-07-21

Found via `/graphify` knowledge-graph audit of `frontend/` + `scripts/` (0 token
cost, code-only AST extraction). Each file below was confirmed dead — not a
false positive — before moving. See DECISIONS.md 2026-07-21 for the full audit
and evidence per file.

**Recall window: 30 days (through 2026-08-20).** If nothing breaks by then,
these can be deleted outright. If something surfaces a dependency on one of
these, `git mv` it back from here rather than reconstructing from scratch —
full history is preserved (moved with `git mv`, not copy+delete).

## What's here and why

- `scripts/merit_api.py`, `scripts/merit_api_v2.py` — untouched since the
  initial commit (2026-05-16), before real project history starts. Point at
  the non-authoritative `meritgiving.db`. CLAUDE.md already documented these
  as "removed" — they just hadn't actually been deleted yet.
- `frontend_flask_integration/merit_api.py` — a "drop this into your Flask
  project" boilerplate blueprint, swept along during the 2026-06-04
  merit→daanaa rename but never wired into the live app.
- `restart_merit_api.sh` — an ops script still targeting `merit_api:app` via
  gunicorn, the exact stale-reference pattern CLAUDE.md calls out by name.
- `scripts/rebuild_from_scratch.py` (v1) — superseded by
  `scripts/rebuild_from_scratch_v2.py`, which is a confirmed superset (adds
  state-code validation, NTEE1 derivation, and filtered-row auditability).
  Both were created in the same minute (2026-06-16); v2 is the one still
  worth keeping. Neither is referenced by cron or `overnight_pipeline.py`.
