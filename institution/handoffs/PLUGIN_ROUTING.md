# Claude Plugin Routing — Week-One Support

Anthropic plugins may assist Claude Code, but repository rules and the shared
handoff remain authoritative. A plugin is an implementation aid, not an
approval authority.

## Recommended routing

### Engineering

Use for:

- backend route implementation;
- tests and type fixes;
- API diagnostics;
- deployment-script review;
- performance and reliability work.

Required evidence:

- exact diff;
- compile/test output;
- rollback plan;
- no manual Gunicorn process;
- no production write without release approval.

### Data

Use for:

- IRS source reconciliation;
- v6 coverage checks;
- database read-only analysis;
- data quality reports;
- backup and integrity verification.

Required safeguards:

- use the authoritative production database path;
- distinguish verified, unverified, revoked, unknown, and exception states;
- never rewrite historical wallet status;
- never expose private donor data;
- do not perform migrations during the unattended week.

### Marketing

Use for:

- donor-facing copy review;
- nonprofit dignity and small-organization language;
- launch or outreach drafts;
- SEO and page messaging suggestions.

Required safeguards:

- no unsupported IRS or deductibility claims;
- no shame, ranking, pressure, or scarcity language;
- clearly distinguish public records, nonprofit-provided information, and AI
  inference;
- drafts only until human approval.

### Productivity

Use for:

- task sequencing;
- daily summaries;
- handoff formatting;
- report organization;
- reminders and checklists.

It must not:

- delete or overwrite evidence;
- mark a task approved without evidence;
- treat an unanswered handoff as approval;
- deploy or restart production services.

## Required plugin handoff

Every plugin-assisted task must append this to the active handoff:

```text
plugin:
task:
files_read:
files_changed:
evidence:
tests:
known_uncertainty:
human_decision_needed:
next_owner:
```

## Conflict rule

If a plugin recommendation conflicts with `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`,
`institution/CONSTITUTION.md`, or the active handoff, follow the higher-order
repository rule and record the conflict. Do not silently resolve it by shipping.
