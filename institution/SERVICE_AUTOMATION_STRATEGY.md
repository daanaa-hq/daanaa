# Service & Onboarding Automation Strategy — AI Customer Service for All

**Authority:** Founder directive 2026-07-12 ("automate customer service and onboarding
for all… the whole AI voice customer service etc."). Strategy locked on the stronger
model; execution tasks feed EXECUTION_HANDOFF_2026_07_12.md.

## Stewardship gates (non-negotiable, decided now)

1. **AI always discloses itself.** Any AI voice or chat agent opens with plain
   disclosure ("You're talking with Daanaa's automated assistant"). Never simulates a
   human. Extends the concierge ruling: "AI is infrastructure, never deception."
2. **Accountability stays human (P10).** Every automated interaction has an escalation
   path to a human (founder initially). AI never makes claim-verification *decisions*;
   it prepares, schedules, answers, and routes.
3. **Privacy (P2).** Voice/chat processed on local inference wherever possible. No
   conversation retention beyond operational need; no caller data to cloud LLMs.
4. **Outbound AI calling is founder-gated.** Inbound answering is fine; AI *initiating*
   calls to nonprofits is trust-sensitive and ships only with an explicit founder ruling.
5. **Small-org dignity (P4).** Phone support matters precisely because the least
   digitally-mature orgs prefer it. Voice is an accessibility feature, not a cost cut.

## What already exists (build on, don't rebuild)

- Twilio integration + `call_sid` plumbing (concierge endpoint), `called_at`/`call_notes`
  columns; Lob letters; PIN claim flow; OrgClaimEditor self-service profile editor.
- Nudge infrastructure: `nudge_sent_at`, `checkin_sent_at`, `profile_nudge_sent_at`
  columns already in org_claims — sequences were anticipated, never automated.
- Grounding corpus: FAQs, guides, methodology, how-it-works (precomputed);
  546K org embeddings + mxbai embedding server (port 11436) → RAG is nearly free.
- Qwen2.5-32B local (port 11437) — the brain, $0/query.
- hello@daanaa.org (warm human voice) — automated mail must match copy-voice rules.

## Phase A — Text-first service automation (execute first; ~$0/mo)

**A1. Grounded support assistant (site chat + email).** Local RAG: question → mxbai
embedding → retrieve from FAQ/methodology/guides corpus → Qwen answers with citations to
the source page → below-threshold confidence routes to hello@daanaa.org. Frontend chat
widget = frontend change → founder reviews diff before deploy.
**A2. Onboarding email sequences.** On claim start: welcome + what-happens-next. On
verification: profile-completion guide + concierge disclosure language. Day 7/30:
nudge/check-in (columns exist). Copy follows kitchen-table voice; every mail from
@daanaa.org; unsubscribe honored structurally.
**A3. Claim-funnel analytics.** Instrument the claim flow steps (Plausible custom
events, privacy-safe, no PII) so drop-off points are visible before we automate more.
**A4. Help center.** Bake existing guides/FAQs into a /help section (precompute like
everything else). Searchable via existing FTS.

## Phase B — Inbound AI voice (after A proves the corpus; ~$1–5/mo Twilio usage)

Twilio number → media stream webhook → home server: Whisper STT (GPU) → Qwen with the
same RAG corpus → local TTS (Piper) → reply. Opens with disclosure. Handles: "how do I
claim my org", claim-status lookups (by callback after identity check), FAQ answers.
Anything else: "I'll have a person call you back" → logs to founder queue with
transcript summary. Latency target <1.5s per turn (achievable on R9700 for 32B — if
p95 misses, fall back to a smaller local instruct model; pre-committed benchmark).

## Phase C — Founder-gated expansions (proposals only, do not build)

- Outbound AI reminder calls (claim PIN expiring, profile incomplete).
- Email-domain auto-verification: claimed-org email domain == `website_final_domain` →
  auto-verify without PIN letter. Big onboarding accelerator, but it CHANGES the trust
  posture of verification (P3) — founder must rule. Prepare a one-page comparison
  (PIN-by-mail vs. domain-email) with fraud scenarios.

## Sequencing & cost

A1–A4 are home-server + existing services: $0/mo fixed. Phase B adds Twilio usage
(inbound minutes, pennies each; log in COST_LEDGER.md when the number goes live).
No new paid SaaS anywhere in this plan. Every phase logs to DECISION_LOG.md and gets a
Learning Record per the Learning Directive.
