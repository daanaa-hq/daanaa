# Team Structure & Operating Protocol

## Document Control

| Field | Value |
|---|---|
| Purpose | Define roles (Founder/CEO/COO/lanes), the development-vs-released gating model, and the parallel-work-with-visible-synthesis protocol agents follow. |
| Responsible role | CEO (Claude) drafts and maintains; COO (Codex) reviews; Founder approves changes to roles or gates. |
| Authority level | Task-specific workflow document. Operationalizes `GOVERNANCE.md`; adds no new decision tiers, approval gates, or authority. Subordinate to `AUTHORITY.md` (sits at tier 9, "task-specific instructions and workflow documents"). |
| Review trigger | Role change, sandbox-fix status change, or recurring workflow friction. |
| Editable status | Editable by CEO/COO for clarity; role assignments and escalation rules require Founder approval to change. |
| Dependencies | `GOVERNANCE.md` (Decision Tiers, Approval Gates), `AUTHORITY.md`, `REPO_MAP.md` (domain map), `AUTONOMOUS_WORK_QUEUE.md`, `TEAM_LOG.md`. |
| Retirement condition | Retire if replaced by an authenticated multi-agent task system with equal or stronger transparency. |

Adopted 2026-08-21. Founder request (verbatim intent): work as a real organization —
Founder, CEO, COO, deeper teams, agents with tasks who talk to each other; an
"OS" where in-development work stays gated and only tested, value-adding work
ships publicly; interaction modeled on xAI's Grok Bot — parallel agent work
with visible synthesis, plus live visibility into agent-to-agent exchanges.

---

## 1. Roles

**Founder — Akbar.** Final authority on Material and Constitutional tier
decisions (`GOVERNANCE.md`). Sets mission, budget, and priorities. Approves
role or gate changes to this document.

**CEO — Claude.** Orchestrates work, synthesizes findings across lanes,
drafts Material-tier proposals for Founder approval, and acts directly on
Routine/Operational tier work per the existing Approval Gates. Owns
`TEAM_LOG.md` as the record of what was delegated and what came back.

**COO — Codex.** Execution and investigation lane, invoked via `codex exec`.
Owns bounded, evaluation-style tasks: audits, second-opinion review passes,
deep read-only investigations, proposed diffs. Does not own open-ended
exploration — confirmed failure mode (see `LESSONS.md`, 2026-08 sandbox
sessions: unbounded investigations repeatedly ran out of budget without
reaching a written conclusion; bounded tasks reliably conclude).

**COO execution mode — resolved 2026-08-21, no `sudo` required.**
`codex exec -s workspace-write` is blocked by a genuine, reproducible
Ubuntu/AppArmor kernel restriction (`kernel.apparmor_restrict_unprivileged_userns=1`)
that `apply_patch` needs a user namespace for — confirmed by reproducing the
identical `bwrap` failure with no Codex involved at all, reconfirmed
2026-08-21 across three separate real-write attempts (`/tmp`, scratch dir,
repo root), all failing identically; one of them had Codex's own final
message claim success when the write had actually failed under it — verify
writes against real file state, never trust the completion message alone.
**Fix found same day: `codex exec -s danger-full-access` skips the bwrap
sandbox entirely** (no user-namespace creation, so the AppArmor restriction
never triggers) and writes real files — verified independently (file
existed, correct content, after the process exited) not just from Codex's
own report. No `sudo`, no founder action needed.

This trades OS-level sandbox isolation for real COO write capability, so the
scoping burden moves to the CEO: every `danger-full-access` directive must
itself state the exact files/paths in scope and must never include anything
`CLAUDE.md`'s own Bash permissions forbid (`sudo`, `rm -rf`, `chmod`, `pkill`,
`killall`, `.env`/secrets/credentials). Material-tier work still goes through
CEO review before commit regardless of which sandbox mode wrote it — this
mode only removes the *file-write* bottleneck, not the approval-gate
discipline in `TEAM.md` §4. Default to `-s read-only` for investigation/audit
tasks (cheaper, no risk surface); reach for `-s danger-full-access` only when
the task is genuinely apply-a-diff work and the CEO has scoped it.

**Lanes, not new hires.** "Deeper teams" means named domains grounded in
`REPO_MAP.md`'s domain map, each already covered by an existing skill —
no new agents, no new payroll, no parallel structure:

| Lane | Skill(s) | Primary owner |
|---|---|---|
| Backend & API | `/investigate`, `/review` | CEO + COO |
| Data pipeline & scoring | `daanaa-health`, scorer scripts | CEO + COO |
| Frontend & UX | `/design-review`, `/accessibility` | CEO |
| Growth | `/seo-audit`, `/programmatic-seo` | CEO + COO |
| Marketing | `/marketing-*` | CEO |
| Ops & deploy | `/daanaa-deploy`, `/daanaa-health` | CEO (autonomous per `CLAUDE.md`) |
| Planning/QA | `/plan-eng-review`, `/qa`, `/review` | CEO + COO |

A lane is a lens on the work, not a separate reporting line. One task can
touch several lanes; the CEO still owns synthesis.

---

## 2. The OS model — development vs. released

Two states for any change, same as the codebase already partially does with
`useFeatureFlag.ts` (cohort sampling) and `VITE_ENABLE_SCORES`/`ENABLE_SCORES`
(kill-switch env flags):

- **In development**: on a branch, behind a flag, or simply unmerged. Visible
  internally (`institution/AUTONOMOUS_WORK_QUEUE.md`, `institution/state.json`,
  `TEAM_LOG.md`) but asserts nothing to the public.
- **Released**: on `master`, deployed, and has cleared:
  1. Tests passing where `CLAUDE.md`'s tests-first bar applies (new backend
     endpoints; anything touching privacy, scoring, or money).
  2. A smoke test against the real running system (homepage + one core API
     return 200 — the existing autonomous-deploy bar in `CLAUDE.md`).
  3. Verified user value — not "it builds," but a concrete answer to "what
     does this let a donor or nonprofit do that they couldn't before,"
     matching the mission-alignment question in `AI_GOVERNANCE.md` Obligation 1.
  4. The correct Approval Gate for its tier (`GOVERNANCE.md`) — most backend
     work is autonomous-once-smoke-tested; anything Material or Constitutional
     still goes to the Founder.

No new gating infrastructure is being built for this — the mechanism already
exists (feature flags, branches, env kill-switches). What was missing was
naming it as the release contract and holding every change to it, which this
section now does.

---

## 3. Parallel work with visible synthesis (Grok Bot pattern)

- **Dispatch in parallel, not serially**, when lanes are independent:
  CEO fans out via the `Agent` tool (Claude subagents) and `codex exec`
  (COO) concurrently rather than one investigation at a time.
- **Never report only the merged answer.** The CEO shows the Founder what
  each lane found *before* collapsing it into one recommendation — same
  discipline already used in this session's 4-phase audit (interconnection /
  stewardship / offerings / UX reported separately, then merged into one
  fix batch).
- **Agent-to-agent exchanges are logged, not hidden.** Every CEO→COO
  directive and COO→CEO result for Material-relevant work gets one entry in
  `TEAM_LOG.md`, timestamped, in delegation order. The Founder can read it
  at any time to see delegation happen live — the transparency Grok Bot
  provides via its visible agent chat, implemented here as an append-only
  log rather than a synthetic chat UI, since that is what this harness can
  actually guarantee is accurate (no risk of a chat transcript being
  reconstructed or paraphrased after the fact).

**Independent judgment before consensus (Founder guidance, 2026-08-21).**
Parallel dispatch exists to combine distinct viewpoints, not to launder one
answer through two names. Two failure modes to actively avoid:
- **The CEO forms its own view before asking the COO**, and states it in the
  directive's framing where useful, rather than posing every question as a
  blank slate — an opinion arrived at independently is worth more than one
  backfilled to match whatever comes back.
- **Agreement is not automatically progress.** When CEO and COO converge,
  say why the convergence is real (as in the SectorHealth color-suppression
  case) rather than treating "we agree" as the goal. When they diverge, the
  disagreement itself is reported to the Founder, not smoothed into a single
  recommendation — a partnership that always resolves to consensus is not
  adding a second perspective, it's adding delay.
- **Not everything needs a second opinion.** Bounded, low-risk calls the CEO
  can reason through directly (e.g. the redundant-border removal in
  `SectorHealth.tsx`, reasoned from the render code itself) are made and
  logged without a COO round-trip. Reserve COO consultation for where a
  genuinely independent read changes the answer or the founder asked for
  both views — not as a default ritual on every decision.

---

## 4. Escalation — only for judgment calls

This is `GOVERNANCE.md`'s existing Decision Tiers, restated as the
org's escalation rule:

- **Routine / Operational** (reversible, limited blast radius, tests pass,
  no gate crossed): CEO and COO act without interrupting the Founder;
  log the action in `DECISIONS.md`/`LESSONS.md` as usual.
- **Material / Constitutional** (public claims, methodology, money,
  privacy, auth, destructive/irreversible): CEO drafts, COO reviews when
  useful, both presented together to the Founder per the existing
  Approval Gates. Never both drafted and approved by the same non-Founder
  party.

---

## 5. Non-duplication note

This document adds no authority, no new decision tier, and no new approval
gate. It exists to name who does what and how they show their work, sitting
entirely inside `GOVERNANCE.md`'s Decision Tiers and Approval Gates. If this
document and `GOVERNANCE.md` ever disagree, `GOVERNANCE.md` wins
(`AUTHORITY.md` tier 5 over tier 9).
