# Board Simulation — 2026-07-18: Five-Item Reliability & Quality Program

**Trigger:** Founder granted autonomous lead and asked pointedly whether the
improvement list I proposed had gone through the governance process before I
presented it. It had not — it was direct engineering judgment. This simulation
is the corrective: the five items go through Gates 1-3 before any of them is
executed, and the answer to "did you go through this process" becomes yes
from here forward.

**The five items:**
1. SLO alert on public search latency (cache-busted probe, >3s twice → alert)
2. Backup restore drill (rehearse restoring from daanaa_backup.sh output)
3. Founder phone QA of the donor flow (never done end-to-end on a real phone)
4. Search-quality golden set (~20 queries with expected-result assertions)
5. State charity registries as a free data source for the no-website pool

## Gate 1 — Principles Check

- **Items 1, 2, 4** are reliability/quality infrastructure. No principle is
  touched negatively; P6 (mistakes corrected quickly) and P9 (explainable)
  are directly served — an unalerted 21s search regression (yesterday's real
  incident) is a P6 failure mode, and an unrehearsed backup is an
  unverified claim to ourselves.
- **Item 4 caution:** the golden set must assert *relevance*, never *rank by
  size or fame* — asserting "Red Cross first for 'disaster'" would quietly
  encode the big-org bias P4 forbids. Assertions must be presence/recall
  shaped ("org X appears in top N for its own name"), not prominence-shaped.
- **Item 3** serves P4 (small orgs' donors are mobile-heavy) and P3 (we claim
  the flow works; we have not verified it as a real user).
- **Item 5** touches P3 (provenance — registry data must be attributed and
  reviewable), P5 (politeness — bulk access must follow each registry's terms;
  our crawler-etiquette decision applies to government sites too), and P1
  (public civic data, aligned with mission). Gate 1 eliminates nothing but
  requires item 5 to return to the board before any ingestion or
  donor-visible use — scoping only for now.

## Gate 2 — Data Validation

- **Item 1:** validated by incident — 2026-07-18 search regression ran at
  15-21s for an unknown period; no alert existed; discovery was the founder
  asking "is search fast." Cost of the fix: one cron + curl probe, zero spend.
- **Item 2:** daanaa_backup.sh was rewritten 2026-07-12 with strict error
  handling, but no restore has ever been rehearsed. An untested backup is a
  hypothesis (Research Directive: treat claims as hypotheses until tested).
- **Item 3:** no record in any session of a full phone walk-through of
  search → org page → donate hand-off → wallet save. Plausible-gap evidence:
  the /org/login funnel dead-ended silently for weeks before 2026-07-18.
- **Item 4:** the 2026-07-17 sort-param bug shipped through a presence-only
  contract test — behavior-shaped assertions are the class of test that would
  have caught it. Golden queries extend that lesson to search quality.
- **Item 5:** unscoped. ~1.9M orgs have no known website; state registries
  (CA, NY, FL, etc.) hold self-reported websites/contacts under varying terms.
  Coverage, format, and terms are unknown → that IS the scoping task.

## Gate 3 — Board Simulation

| Seat | Position |
|---|---|
| **Legal** | Items 1-4: no exposure. Item 5: terms-of-use review is mandatory per registry before any bulk access — some state AG sites prohibit scraping; several offer bulk downloads or open-data portals, which are the only acceptable paths. Scoping must produce a per-state terms table. |
| **Accounting/Finance** | All five are zero-spend (local compute, founder time). Item 2 protects the single most valuable asset (the enriched registry DB). Strong support for 1 and 2. |
| **Marketing** | Item 1 protects the first impression — a donor who hits a 20s search never comes back. Item 3 is the mobile reality check; most social/carousel traffic is mobile. Supports 3 being scheduled with the founder soon, not left open-ended. |
| **ED (nonprofit leaders)** | Item 5 is the seat's priority: the 1.9M no-website orgs are overwhelmingly small — finding their sites through registries they already file with is P4 in action. Accepts scoping-first discipline. |
| **Donor group** | Items 1 and 4 are the donor-facing ones: fast search that returns the right orgs is the product. Golden set should include misspellings and city-level queries, because that is how real donors type. |
| **Stewardship chair** | Approves 1, 2, 4 for immediate autonomous execution — they are self-verification infrastructure, the system checking its own honesty (P3 applied to ourselves). Item 3 approved but requires the founder; prepare the checklist, don't nag. Item 5: scoping only; ingestion and any donor-visible promotion return to the board with the terms table and a provenance plan. Notes with approval that the founder's process question was itself a governance catch — record the lesson: proposals to the founder go through gates BEFORE presentation, not after. |

**Consensus:** Unanimous approval of items 1, 2, 4 for immediate execution;
item 3 approved pending founder availability (prep now); item 5 approved as
scoping-only with mandatory board return before ingestion.

**Confidence to proceed:** 1, 2, 4 → 95%. 3 → 90% (founder-gated).
5 → 85% for scoping (0% for ingestion until terms are reviewed).

## Gate 4 — Resolution

No split → no escalation needed. Recorded in governance/DECISION_QUEUE.md.
Execution order: 1 (SLO alert), 2 (restore drill), 4 (golden set), 3 (checklist
prep), 5 (scoping) — ordered by incident-proven risk first.
