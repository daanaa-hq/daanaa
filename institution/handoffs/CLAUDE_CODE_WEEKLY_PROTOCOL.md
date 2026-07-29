# Claude Code Remote Operating Protocol — One Week

## Purpose

Claude Code is the remote implementation and testing agent while Codex is
temporarily unavailable for direct remote access. The repository is the shared
record. Claude Code must read the current queue before acting and must write a
handoff before stopping.

## Authority boundary

Claude Code may inspect, edit, test, document, and prepare local changes.

Claude Code must stop before:

- deploying to the droplet or Cloudflare;
- changing production databases or scoring data;
- changing authentication, payments, privacy, or public methodology;
- deleting backups, artifacts, or user data;
- publishing donor-facing copy without the required review evidence.

Production deployment requires a separate explicit release record naming the
exact commit, verified backup, rollback command, smoke tests, and owner approval.

## File ownership

Before editing, Claude Code writes its name, task, and timestamp to the active
handoff file. It must not edit a file listed as owned by another active task.

Codex review files are advisory until the next handoff is written. Do not infer
approval from silence.

## Daily loop

1. Read `AGENTS.md`, `CLAUDE.md`, this protocol, and the active handoff.
2. Inspect `git status` and the exact current diff.
3. Claim one queue item only.
4. Make the smallest reversible change.
5. Run the listed tests and save outputs in `.release_coordination/reports/`.
6. Stop at the checkpoint and take the scheduled break.
7. Update the handoff with status, evidence, risks, and next owner.
8. Do not start another queue item if a P0/P1 failure remains.

## Required handoff fields

```text
date_utc:
agent: claude-code
task:
status: in-progress | blocked | ready-for-review
files_changed:
tests_run:
tests_passed:
tests_failed:
known_risks:
rollback:
next_action:
codex_review_needed:
```

## Week-one priorities

### Priority 1 — Local backend correctness

- Keep parser repairs separate from the v6 route addition.
- Confirm the actual production entrypoint is `droplet_api:app`.
- Confirm the v6 endpoint returns JSON locally for direct, peer-reference,
  limited-data, and invalid-EIN cases.
- Do not copy files to the droplet.

### Priority 2 — Org-page stewardship and accessibility

- Test 375px, 768px, desktop, light mode, and dark mode.
- Verify IRS status and v6 peer context remain separate.
- Never show peer statistics as organization-specific facts.
- Preserve respectful language for small and data-limited organizations.
- Verify revoked organizations have no donation CTA.
- Verify keyboard focus, skip link, labels, contrast, and touch targets.

### Priority 3 — Regression and release evidence

- Resolve or formally document the six existing frontend test failures.
- Run build, type check, backend tests, and design/accessibility checks.
- Preserve all reports and screenshots.
- Prepare—but do not execute—a droplet release plan.

## Stop conditions

Stop and write `blocked` if:

- the current diff contains unexpected files;
- a test fails for a newly changed path;
- a source or count conflicts with the IRS evidence record;
- a donor-facing phrase implies deductibility or certainty without evidence;
- a deployment, backup, or database decision is required;
- the droplet service becomes unhealthy.

## Handoff location

- Active queue: `institution/handoffs/2026-07-29-v6-local-release.md`
- Daily notes: `institution/handoffs/daily/`
- Test artifacts: `.release_coordination/reports/`
- Browser evidence: `.release_coordination/artifacts/`

Claude Code should commit only when the owner explicitly requests a commit.
Otherwise, leave the worktree reviewable and record the exact diff.
