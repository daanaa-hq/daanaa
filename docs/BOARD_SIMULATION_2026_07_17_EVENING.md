# Board Simulation — 2026-07-17 Evening Cycle

Run per `docs/DECISION_WORKFLOW.md` over all 5 open items in
`governance/DECISION_QUEUE.md`. Six seats: Legal, Accounting/Finance,
Marketing, ED (nonprofit leaders), Donor group, Stewardship chair.

Gate 2 data gathered before this simulation:
- Charity Navigator Terms of Use fetched and read (2026-07-17)
- web_finder 10K run interim results: 371 verified / 2,484 processed (~15%)
- Live terminology census on donor-facing pages (post-cleanup)
- CN footprint in our database: 1 link total; API fallback unkeyed and inert

---

## Item 1 — Charity Navigator fallback (live API checks?)

**Data:** CN's Terms of Use, Section 3, prohibits "data mining, robots, or
similar data gathering and extraction methods," republishing without express
written consent, and competitive use. Our existing fallback calls their v2
API without a key and has produced exactly 1 link. Separately,
phase_orchestrator was configured to AUTO-ACTIVATE `cn_rate_limited_scraper.py`
on Phase-1 saturation — automated website scraping, squarely prohibited.

**Legal:** Hard no on scraping — the ToS could not be clearer. The unkeyed
API calls are also not a sanctioned pathway. The auto-activation of a scraper
was a landmine: it would have started a ToS violation with no human in the
loop. Disable immediately. The only clean path is CN's official API program
with written consent.

**Finance:** The entire CN dependency yielded 1 link. Retiring it costs
nothing measurable.

**Marketing:** CN is a potential future partner; scraping them would burn
that bridge permanently. Walk away clean.

**ED:** No partner impact either way.

**Donor group:** Donors care that links work, not where they came from.

**Stewardship chair:** P7 (independence) cuts deeper than compliance: leaning
on a rating platform's data is philosophically off-brand — they grade, we
don't. Our own verification pipeline is the honest path.

**RESOLUTION (unanimous):**
1. Phase 2b scraper auto-activation permanently disabled (done this cycle).
2. CN API fallback retired from the discovery daemon (done this cycle).
3. If CN data is ever wanted: official API program + written consent + founder
   approval. Until then, we discover and verify links ourselves.
- Confidence: 100%. No founder escalation needed (protective action, zero cost).

---

## Item 2 — Donor-facing terminology glossary

**Data:** Post-cleanup census on the two highest-traffic pages: "rank" 0,
"percentile" 0 (today's removals eliminated them), "score" 6, "context" 7,
"tier" 16 (mostly the visibility-tier filter in the directory). Drift is now
modest but real — three terms describe one concept.

**Legal:** Consistency reduces misrepresentation risk. Approve a governed list.
**Finance:** Terms must match what the data supports — "context" is accurate,
"score" overstates. Prefer "financial context" everywhere donors see it.
**Marketing:** One vocabulary, donor-plain: "financial context," "health
signal," "peer context." Avoid introducing new jargon in the fix.
**ED:** Any term must pass the kitchen-table test read as the org being
described. "Context" passes; "score" is borderline; "tier" reads as grade.
**Donor group:** Donors already understand "health" and "context" instantly.
**Stewardship chair:** This is LANGUAGE_AND_MINDSET.md becoming enforceable.

**RESOLUTION (consensus, escalate for approval):** Draft glossary —
- "financial context" (replaces bare "score" in donor-facing copy)
- "health signal" (HEALTHY/STABLE/NEED_SUPPORT, unchanged)
- "peer context" (comparisons within archetype+band cells)
- "visibility tier" — flagged: directory filter still exposes tiers donor-side;
  recommend renaming the filter or removing it in a follow-up (consistent with
  the profile tier retirement)
- Lint test enforces the avoid-list (rank, grade, top-rated, failing, at-risk)
  in `frontend/src` donor-facing strings.
**→ ESCALATED to founder:** approve the term list + decide the directory
visibility-tier filter's fate. Confidence in draft: 85%.

---

## Item 3 — AI-output human-review policy

**Data:** Current practice: missions/cause tags batch-generated and
batch-reviewed; AI-found links auto-verified + labeled "found by AI, not yet
confirmed by the organization"; scores deterministic (no LLM); outbound comms
gated by comms-steward.

**All seats converged quickly. Policy adopted:**
1. **New claim types** (any new kind of AI-derived statement about an org)
   require human review before FIRST publication; thereafter automated with
   sampling.
2. **Per-item outputs at scale** (missions, links, tags): automated
   verification + honest provenance label + Mistake Registry corrections path
   + monthly sample audit (100 items/type).
3. **Anything on the giving path** (donate links): content verification
   pipeline mandatory (already live — reverify_donate_pages pattern).
4. **Outbound communications**: comms-steward three-read gate, no exceptions.
5. **Scoring**: stays deterministic; any LLM involvement in scoring would be
   a principle change requiring founder + charter review.

**RESOLUTION (unanimous):** Adopted as policy; documents current practice
plus the sampling cadence. No founder gate (P10 codification). Confidence: 95%.

---

## Item 4 — Full-backend vs droplet contract drift guard

**Data:** The 2026-07-05 outage was this failure class. Today's verification
error (agent hit `/api/org/` instead of `/api/organizations/`) shows even
maintainers trip on surface differences.

**All seats:** engineering necessity, no values tension.

**RESOLUTION (unanimous):** Build a contract test asserting the shared API
surface (route list, status codes, key response fields, security headers)
matches between daanaa_api.py and droplet_api.py; wire into the principle
test suite. Add the audit's terminology lint in the same suite. Backend
autonomy covers implementation. Confidence: 95%.

---

## Item 5 — web_finder 14–15% success rate

**Data:** Interim 10K run: 371 verified / 2,484 processed (~15%). Zero
robots-blocked, zero no-candidates. Failure inspection shows the miss pattern:
high-revenue orgs failing verification mostly HAVE websites at domains our
name-token guesser never generates (e.g., "Vermont Land Trust Inc" →
vlt.org, an acronym domain). Verification is not too strict — candidate
generation is too narrow.

**Finance:** 15% precision-first yield at zero marginal cost is acceptable;
raising recall via better candidates is cheap (local LLM).
**Legal:** Keep robots.txt respect and identified UA exactly as is.
**Stewardship chair:** P3 demands we NEVER loosen verification — a wrong
website attributed to an org is worse than none. Improve candidates, not
thresholds.
**Marketing/ED/Donor:** More real websites = more give-paths; no concerns.

**RESOLUTION (unanimous):** Success rate is acceptable for v1 BUT improvable:
1. Keep ownership verification thresholds unchanged.
2. Add LLM candidate generation (Qwen on 11437 proposes acronym/abbreviation
   domains from org names) as a second candidate tier.
3. Re-measure after the enhancement; revisit only if still <20% with enriched
   candidates.
Confidence: 90%.

---

## Cycle summary

| Item | Outcome | Founder needed? |
|---|---|---|
| CN fallback | Resolved — scraper disabled, fallback retired | No (FYI only) |
| Terminology glossary | Draft ready | **Yes — approve terms + tier-filter fate** |
| AI review policy | Adopted | No |
| Contract drift guard | Approved — build it | No |
| web_finder rate | Keep verification, improve candidates | No |

Queue after this cycle: 4 resolved, 1 escalated. Nothing older than 24h.
