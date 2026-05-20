# Skills Registry

**All active skills, their versions, and refresh status.**

Update this when adding, refining, or retiring a skill.

---

## Active skills (Phase 0)

| Skill | Version | Last refined | Usage count | Notes |
|---|---|---|---|---|
| prompt-caching | 1.0.0 | 2026-05-19 | 0 | Foundation; deploy immediately |
| repo-map | 1.0.0 | 2026-05-19 | 0 | Implement when codebase > 20 files |
| token-efficiency | 1.0.0 | 2026-05-19 | 0 | Reference for all agents |
| irs-bmf-ingest | 1.0.0 | 2026-05-19 | 0 | Activate at Week 6 |
| name-validation | 1.0.0 | 2026-05-19 | 0 | TASK 1 — run this week |

## Skills queued for Phase 0

To be created as needed during build:

- `propublica-enrich` — ProPublica API integration with attribution
- `ein-profile-page` — Profile page rendering for any EIN
- `badge-scoring` — Calculate badges per scoring rules
- `giving-wallet-ui` — Client-side giving wallet preview
- `tip-jar-stripe-link` — Configure Stripe Payment Link for tips
- `legal-disclosure-snippets` — Verbatim approved legal language
- `ntee-confidence` — NTEE classification confidence scoring
- `newsletter-curator` — Weekly newsletter draft generation
- `morning-brief-template` — Standard brief structure

## Skills queued for Phase 1

- `claim-verification-flow` — End-to-end claim verification
- `physical-mail-via-lob` — Mail OTP codes via Lob MCP
- `dns-txt-verifier` — Domain control verification
- `acknowledgment-letter-automation` — Tax receipt drafts (verified claimants only)
- `compliance-watchdog` — Educational filing reminders (NOT legal advice)

## Skills queued for Phase 2

- `vendor-matchmaker` — GPO recommendations
- `savings-tracker` — $ saved per nonprofit tracking
- `sector-report-generator` — Quarterly report drafting
- `impact-storyteller` — Story drafting partner for nonprofits

---

## Conventions

### Skill file structure
```
merit-platform/.claude/skills/[skill-name]/
├── SKILL.md          # the canonical skill definition
├── examples/         # example uses (optional)
├── tests/            # test cases (when applicable)
└── CHANGELOG.md      # version history (when v2+)
```

### Skill front matter
```yaml
---
name: [skill-name]
version: 1.0.0
last_updated: YYYY-MM-DD
status: active | scaffold | deprecated
phase: 0 | 1 | 2
owner: [department head agent]
---
```

### When to create a new skill
- Capability gap appears 3+ times
- A pattern is reusable across multiple agents
- A specific tool integration needs documented best-practice
- An external pattern (cookbook, repo) is worth codifying

### When to retire a skill
- No usage in 2 quarters
- Replaced by better skill or external tool
- Tied to deprecated pattern (e.g., specific model behavior)

Retired skills move to `.claude/skills/_archive/` (still readable, not active).

---

## Refresh cadence

- Quarterly: `/model-upgrade-check` reviews all skills
- After 100 uses: review and refine
- After capability gap closes via skill: confirm skill quality
- Annually: full skills library audit

---

## Quality signals per skill

For each skill, track:
- Usage count (from claude_calls table, tagged by skill)
- Average cost when used (should trend down)
- Quality score impact (output quality when skill applied vs. not)
- Gap closure rate (how often does the skill prevent re-asks)

These metrics feed into `/refine-skill [name]` decisions.
