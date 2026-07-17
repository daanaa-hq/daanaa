# Daanaa Custom Skills

The operational skill set behind Daanaa — infrastructure for giving.
Every skill serves one goal: **make giving easy** for donors while treating
every nonprofit, from a kitchen-table pantry to a national institution, with
equal dignity.

Two documents govern everything here:

- **`governance/VISION_GIVING_INFRASTRUCTURE.md`** — what we're building and why
- **`governance/LANGUAGE_AND_MINDSET.md`** — how we talk about nonprofits:
  context not verdicts, invitations not judgments, no ranking, no grading,
  no shame. The kitchen-table test applies to every output of every skill.

Also binding: `STEWARDSHIP.md` (11 principles) and `PRIVACY-INVARIANTS.md`.

---

## The skills

### Data & scoring rails

| Skill | Purpose | Key guardrail |
|---|---|---|
| **score-orgs** | Runs the v5 financial context scorer (archetype × revenue band peer cells) | Signals are peer context, never grades; unscored ≠ penalized |
| **precompute** | Builds the static site payload the production edge serves | Public-eligibility filters on every path; honest labels ride with the data |

### Communications & growth

| Skill | Purpose | Key guardrail |
|---|---|---|
| **comms-steward** | Reviews EVERY outbound message before send | Three-read gate: factual honesty → voice → pressure/shame/urgency check |
| **marketing-carousel** | LinkedIn carousel creation + posting | Stewardship gate: insight that encourages giving, never judgment or exposure of struggling orgs |
| **marketing-content** | Content calendar + post ideas from live platform data | Stats quoted must be real and current (P3) |
| **marketing-outreach** | Outreach email/DM drafting (hello@daanaa.org) | Warm, human, no manufactured urgency; @daanaa.org aliases only |
| **marketing-weekly** | Weekly sprint orchestrator (carousel + outreach + analytics) | Composes the above, inherits all gates |

### Governance & quality

| Skill | Purpose | Key guardrail |
|---|---|---|
| **daanaa-system-audit** (`.agents/skills/`) | Full-system audit: architecture, workflows, gap register | Findings framed against charter invariants (e.g., "no payment flow" is P8 by design, not a gap) |

---

## Rules for adding or editing skills

1. **Vision first.** A new skill must state which friction in the giving path
   it removes (see the friction table in VISION_GIVING_INFRASTRUCTURE.md).
2. **Language gate.** Any skill that produces donor- or org-facing words must
   reference LANGUAGE_AND_MINDSET.md and pass the kitchen-table test.
3. **Evidence gate.** Any skill that surfaces claims about an org must trace
   to public data or carry an honest "found by AI, not yet confirmed" label.
4. **Keep them current.** Stale skills are dangerous (a pre-v5 version of
   score-orgs pointed at an archived legacy scorer). When the platform moves,
   the skill moves in the same commit.
5. **Sync the archive.** Material changes here get mirrored to the private
   `daanaa-hq/daanaa-ai-stewardship` repo (sanitize infra details: droplet IP
   → `YOUR_DROPLET_IP`). That repo is the share-with-partners vehicle and
   never goes public without founder approval.
