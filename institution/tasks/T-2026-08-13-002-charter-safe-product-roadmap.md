# T-2026-08-13-002 — Charter-Safe Product Roadmap and Execution Program

| Field | Value |
|---|---|
| Identifier | T-2026-08-13-002 |
| Date opened | 2026-08-13 |
| Owner | Codex (product/program execution), Claude Code (parallel implementation), Founder (approval gates) |
| Scope | Convert the current Daanaa product into a donor-, volunteer-, and nonprofit-centered experience using charter-safe UX, IA, performance, trust, opportunities, and retention improvements. |
| Affected paths | `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/data/`, `frontend/src/hooks/`, `tests/`, `docs/`, `institution/` |
| Higher-authority constraints checked | `AGENTS.md`, `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`, `institution/CONSTITUTION.md`, `institution/AUTHORITY.md`, `institution/CORE_PLATFORM_DEFINITION.md` |
| Status | IN PROGRESS — planning and shadow execution authorized |
| Validation plan | Repo-visible roadmap, implementation batches, live-path QC, a11y/perf checks, governance gate review before production-sensitive changes |
| Review notes | This task may produce code under Track A only. Track B stops at specification until explicit approval. |
| Handoff target | Claude Code |
| Merge or close-out note | Close when Track A batch plan is complete, first implementation batch is delivered or queued, and Track B approval gates are clearly documented. |

---

## Objective

Build toward a Daanaa experience that does four things better than the current product:

1. Help a visitor move from concern to confident action.
2. Help a nonprofit become easier to understand, trust, and support.
3. Make giving money, time, skills, and effort feel natural.
4. Give users strong reasons to come back without becoming a newsletter, social feed, or crowdfunding host.

This work is inspired by competitor strengths, especially structured decision support, but must remain distinct from corporate prospecting products and must not drift into rating-agency behavior.

---

## Product Truth Observed

The current repo already contains most of the raw ingredients:

- strong public-record backbone
- directory, search, org detail, wallet, volunteer, and nonprofit claim surfaces
- methodology and stewardship framing
- large nonprofit universe and growing website coverage

The main gap is not missing product ambition. It is fragmentation:

- discovery is broad but not clearly intent-led
- org pages are information-rich but not yet organized as decision pages
- nonprofit value exists but is not yet presented as a coherent clarity layer
- volunteer pathways exist but are not first-class in the main discovery journey
- trust signals exist but need clearer provenance and more consistent labeling
- return value is not yet strong enough to support retention on product merit alone

---

## Track A — Safe To Execute Now

These workstreams are aligned with the charter and can be designed, specified, implemented, and tested without additional governance approval, provided they remain additive and reversible.

### A1. Discovery IA Rebuild

Goal:
- Make the homepage and directory clearly support `give`, `volunteer`, `research`, `compare`, and `find local`.

Work:
- simplify homepage entry paths
- reduce duplicate search behaviors and unnecessary network work
- improve directory filter hierarchy and mobile scanability
- strengthen `near me`, cause, and intent-first discovery

Acceptance criteria:
- first-screen choices are understandable without reading methodology first
- directory query path avoids redundant fetch patterns where feasible
- mobile discovery remains usable at 375px
- no charter conflicts around ranking, visibility, or paid treatment

### A2. Decision-Grade Organization Pages

Goal:
- Reorganize org pages around decision support rather than raw record display.

Work:
- strengthen the header summary
- separate `what records show` from `what the nonprofit says` and `what Daanaa infers`
- improve evidence layout, filing freshness, trust context, and action CTAs
- add related organizations / network context where data exists

Acceptance criteria:
- provenance is explicit at section level
- a first-time donor can understand the org's mission, scale, status, and next actions quickly
- no AI or derived text is presented as public-record fact

### A3. Nonprofit Clarity Layer

Goal:
- Make nonprofit-facing value legible and useful without corrupting public truth.

Work:
- specify claim/edit flow improvements
- define structured nonprofit-supplied fields
- define correction and clarification workflows
- map these flows to the existing stewardship requirement that corrections remain visible and public truth remains distinct

Acceptance criteria:
- claim flow is understandable
- nonprofit-supplied data is labeled distinctly
- correction workflow preserves auditability

### A4. Opportunities, Volunteer, and Action Layer

Goal:
- Make giving money, time, skills, and effort a first-class path, not a side route.

Work:
- define `Opportunities` as a first-class product surface for claimed nonprofits
- support default `unrestricted support` opportunities
- support `volunteer`, `skilled help`, and `in-kind help` opportunities
- specify `restricted purpose` opportunities separately, with tighter governance review before activation
- improve volunteer discovery entry points
- tighten action CTAs on org pages
- connect `I care about this` to concrete next steps

Acceptance criteria:
- action paths are visible in homepage, directory, and org detail experience
- opportunity provenance is explicit: nonprofit-posted vs public-record vs inferred
- all donate actions route to the nonprofit's own verified destination, not Daanaa custody
- volunteer interest capture stays privacy-safe
- no confusion between Daanaa and the nonprofit's own systems

### A5. Trust, Accessibility, and Performance Hardening

Goal:
- Raise quality to production standard before expansion.

Work:
- remediate live-site contrast failures
- continue semantic and keyboard fixes
- expand live-path Playwright coverage
- keep performance work tied to real user journeys, not synthetic vanity metrics

Acceptance criteria:
- serious accessibility regressions are reduced or eliminated on priority routes
- homepage, directory, and org detail have stable QC coverage
- measurable regressions are documented before shipping

### A6. Retention Without Surveillance

Goal:
- Make the product worth revisiting because it remains useful, relevant, and trustworthy.

Work:
- define return loops driven by saved intent, trusted discovery, and fresh nonprofit-posted opportunities
- design revisit reasons around local relevance, cause relevance, and followable opportunities
- avoid newsletter-style or guilt-driven retention patterns

Acceptance criteria:
- the product offers clear reasons to return that align with donor, volunteer, and nonprofit needs
- retention mechanisms do not depend on spam, guilt, or surveillance
- return paths respect structural privacy commitments

---

## Track B — Specification Only Until Approval

These items can be researched and specified now, but they must not be activated in code or production behavior without explicit founder/governance approval.

### B1. Ranking or visibility logic changes
- any logic that changes which organizations are surfaced first
- any default ordering that could be interpreted as evaluative treatment

### B2. Public badges, scoring, or evaluative methodology
- new badges or labels that imply judgment
- any change to public comparative methodology

### B3. Monetization touching exposure or treatment
- placement, sponsorship, premium profile treatment, or exposure-linked upgrades

### B4. New AI evaluative judgments
- summaries or labels that users could reasonably read as a rating, endorsement, or warning

### B5. Production migrations or deployments
- any schema/data migration
- any public deployment

### B6. Private nonprofit data expansion
- any collection, retention, or display model beyond current stewardship boundaries

### B7. Restricted opportunity activation
- any launch of restricted-purpose giving opportunities without a clear policy for:
  - purpose definition
  - official destination URL
  - overfunding handling
  - timeframe and completion state
  - auditability of nonprofit-supplied claims

---

## Proposed Execution Batches

### Batch 1 — Discovery Foundation

Scope:
- homepage intent framing
- directory interaction cleanup
- performance and accessibility fixes on discovery routes

Primary files:
- `frontend/src/pages/Home.tsx`
- `frontend/src/pages/Directory.tsx`
- `frontend/src/components/SearchBar.tsx`
- related layout/token/components as needed

Done when:
- discovery routes are clearer, faster, and easier to scan
- duplicate search/network behaviors are reduced
- critical accessibility findings on priority paths are addressed or formally deferred

### Batch 2 — Organization Decision Page

Scope:
- org page information hierarchy
- provenance labeling
- action row clarity
- filing/source/freshness presentation

Primary files:
- `frontend/src/pages/OrganizationDetail.tsx`
- related org detail components

Done when:
- org page clearly answers `what is this org`, `how can I help`, and `what is sourced from where`

### Batch 3 — Nonprofit Clarity and Claim Flow

Scope:
- claim/editor IA
- nonprofit-provided data blocks
- correction and attest flow clarity

Primary files:
- `frontend/src/pages/OrgClaimEditor.tsx`
- nonprofit dashboard/profile components

Done when:
- nonprofit value is coherent and provenance-safe

### Batch 4 — Opportunities, Volunteer, and Action Experience

Scope:
- claimed-nonprofit opportunity publishing model
- volunteer search and action surfaces
- org-level volunteer CTAs
- mobile action behavior

Done when:
- unrestricted opportunities are safely specified and/or implemented
- volunteering is visible as a primary path without degrading donor research clarity
- restricted opportunities remain behind governance review unless explicitly approved

### Batch 5 — Retention Without Becoming A Newsletter

Scope:
- return loops based on saved intent, trusted discovery, and fresh nonprofit-posted opportunities
- revisit reasons that are useful without turning Daanaa into a newsletter, feed, or pressure engine

Done when:
- the product gives users credible reasons to return
- retention mechanisms align with privacy and stewardship rules

---

## Research Inputs Already Incorporated

- Cause IQ: strong structured decision support, network context, filing navigation
- Candid: diligence-grade source completeness and nonprofit-supplied profile layer
- Charity Navigator: donor education and trust framing
- GreatNonprofits: human trust texture
- VolunteerMatch / Idealist: action-fit and volunteer intent capture
- behavioral science on identity, reciprocity, friction, volunteering, and motivation crowding

What Daanaa should emulate:
- structure
- evidence navigation
- clearer action paths
- concrete opportunities tied to real needs, not vague support asks
- return value based on relevance, not nagging

What Daanaa should not emulate:
- pay-to-win treatment
- blurred provenance
- judgment presented as objective truth
- crowdfunding mechanics that make Daanaa behave like a money custodian or hype engine
- surveillance-heavy retention

---

## Open Risks

1. Existing in-flight repo changes may touch the same surfaces, especially `Home`, `Directory`, and org-detail routes.
2. Some current product language may imply product commitments that need tightening before visual refinement.
3. Accessibility debt is broad enough that route-by-route prioritization is required.
4. Competitor-inspired features can drift into methodology changes if not carefully scoped.
5. Retention work can easily drift into spam or tracking unless explicitly constrained.

---

## Immediate Next Actions

1. Complete the roadmap handoff note for Claude Code.
2. Start Batch 1 shadow work against homepage and directory.
3. Draft a behavioral-science-backed `Opportunities` spec covering unrestricted vs restricted support and retention loops.
4. Keep all production, migration, and methodology-affecting changes behind explicit approval gates.
