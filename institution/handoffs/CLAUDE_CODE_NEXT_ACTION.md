# Claude Code — Next Action

Read first:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `institution/handoffs/README.md`
4. `institution/handoffs/CLAUDE_CODE_WEEKLY_PROTOCOL.md`
5. `institution/handoffs/2026-07-29-v6-local-release.md`

## Current assignment

Status: ready-to-start
Owner: Claude Code
Scope: local-only v6 backend route, parser validation, and org-page QA

### Step 1 — Inspect

```bash
git status --short
git diff -- droplet_api.py frontend/src/pages/OrganizationDetail.tsx
python3 -m py_compile droplet_api.py
```

### Step 2 — Separate changes

Keep these as separate reviewable changes:

- Change 0: only the five required parser `pass` repairs;
- Change 1: only the v6 route in `droplet_api.py`;
- Change 2: only the approved `OrganizationDetail.tsx` placement/spacing work.

Do not deploy, restart services, modify production databases, or use manual
Gunicorn commands.

### Step 3 — Test locally

Run the coordination phases one at a time:

```bash
OWNER=claude PHASE=inventory bash scripts/local_release_coordination.sh
OWNER=claude PHASE=backend_syntax bash scripts/local_release_coordination.sh
OWNER=claude PHASE=backend_tests bash scripts/local_release_coordination.sh
OWNER=claude PHASE=frontend_tests bash scripts/local_release_coordination.sh
OWNER=claude PHASE=stewardship bash scripts/local_release_coordination.sh
OWNER=claude PHASE=design_accessibility bash scripts/local_release_coordination.sh
OWNER=claude PHASE=local_api bash scripts/local_release_coordination.sh
```

If a phase fails, stop. Do not remove a lock to hide a failure. Record the
failure in the active handoff and wait for Codex review.

### Step 4 — Write the handoff

Update `institution/handoffs/2026-07-29-v6-local-release.md` with:

- exact files changed;
- commands and results;
- test failures, including whether they are pre-existing;
- screenshots or artifact paths;
- unresolved risks;
- next action;
- whether Codex review is required.

Then create a dated daily note under `institution/handoffs/daily/`.
