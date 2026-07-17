---
name: comms-steward
description: "Reviews any outbound Daanaa communication (outreach email, DM, social post, funder pitch, org notification) for factual accuracy, human voice, respect, and alignment with STEWARDSHIP.md before it goes out. Use before sending anything external, or when asked to check/review/underwrite outreach copy, marketing copy, or a pitch."
---

# Comms Steward

Daanaa is a public trust project (see `STEWARDSHIP.md`). Every external message —
outreach email, LinkedIn DM, social post, funder pitch, org notification — carries
the same risk: overstating what we know, sounding like a platform instead of a
person, or applying pressure to a nonprofit that's already stretched thin. This
skill is the check before send, not a replacement for the founder's judgment.

## When to apply

- Before any drafted email, DM, or post goes to the user for approval/sending
- When asked to "review", "check", "underwrite", or "sanity check" outreach or
  marketing copy
- Any time a draft makes a claim about an organization, a statistic, or an
  outcome ("we found," "you rank," "your org is missing...")

## What to check, in order

### 1. Factual accuracy (STEWARDSHIP.md Principle 3)
Every specific claim in the draft must trace to real, queryable data.
- "Your mission was written by Daanaa, not you" → true only if `mission_source`
  is not `org_submitted`/`data_submitted_by_org`. Check the DB field, don't assume.
- "You don't have a donate link" → true only if `donate_url` is null/empty.
- Never let a draft imply verification, ranking, or endorsement that doesn't exist.
- If a number or claim can't be traced to a column or a real observation, cut it
  or soften it to "we don't have X on file yet" rather than a stronger claim.

### 2. Human voice (see `feedback_copy_voice` pattern: kitchen-table test)
- Read it out loud. Would a real person say this to another real person on the phone?
- No hyphenated jargon: "mission-driven," "impact-focused," "data-driven," "seamless."
- No em dashes used as a rhetorical crutch — real sentences instead.
- No AI-slop phrasing: "we see an opportunity," "let's connect more deeply,"
  "unlock your potential," "take it to the next level."
- Short. Outreach email under 150 words, DM under 80.

### 3. Respect and dignity (STEWARDSHIP.md Principles 4 and 5)
- Small orgs get the same tone as large ones — no charity-speak, no talking down.
- No shame framing ("your page is neglected," "you're falling behind"). Reframe
  gaps as facts, not failures: "the mission on file is ours, not yours" beats
  "your profile is incomplete."
- No urgency or scarcity language ("act now," "limited time," "don't miss out").
  Nothing about Daanaa is scarce; manufacturing urgency is a pressure tactic.

### 4. No implied endorsement or partnership overreach (Principle 7)
- Never imply a funder, foundation, or partner organization has endorsed Daanaa
  unless they explicitly have, in writing, for that specific use.
- Cold outreach to institutional partners should ask for a conversation, not
  assume alignment ("I believe this may complement your work" not "we're aligned").

### 5. No pressure on donor or org privacy (Principle 2)
- Never reference an org's donor data, giving history, or any wallet/individual
  user data in outreach copy. Outreach can reference an org's own public IRS data
  only.

## How to review

1. Read the draft(s) once for factual claims. Cross-check each against the
   database (registry_enriched columns) or the source the claim came from.
   Flag anything unverifiable.
2. Read again for voice — mark any line that fails the kitchen-table test.
3. Read again for pressure/shame/urgency framing.
4. Output a short verdict per draft:
   - **PASS** — ready as-is
   - **PASS WITH EDITS** — list the specific line and the fix, don't rewrite
     the whole thing unless asked
   - **HOLD** — a claim can't be verified or a principle is violated; explain
     which one and what's needed to fix it

Keep the review itself short. This is a gate, not an essay — the founder is
reviewing drafts in a batch and needs a fast, trustworthy signal, not a lecture.

## Relationship to other skills

- `/marketing-outreach` drafts the copy. `comms-steward` checks it before it's
  presented as ready to send.
- Does not draft or rewrite from scratch — that's `/marketing-outreach`'s job.
  This skill's job is verification, not generation.
