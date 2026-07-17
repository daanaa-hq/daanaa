# Gap Register

## Highest-confidence gaps

| Title | Severity | Type | Evidence |
|---|---|---|---|
| Vocabulary drift across score/context/tier/ranking language | High | UX / AI governance | Homepage, directory, API types, and stewardship docs use overlapping terminology |
| Production-edge and full-backend behavior can diverge | High | Architecture / Reliability | `daanaa_api.py` vs `scripts/droplet_api.py` split; multiple lessons mention drift |
| Some workflows are visible in scripts but not yet confirmed as end-to-end product features | Medium | Product / Reliability | volunteer, analytics, enrichment, and learning schemas |
| No confirmed payment processor flow in the platform itself | High | Security / Product boundary | Principle tests reject payment SDKs and webhook routes |
| Search, claims, and wallet are well covered, but wider scripts lack direct regression tests | Medium | Testing | Many scripts in `scripts/` |

## AI Language and Decision Governance

| Title | Severity | Type | Evidence |
|---|---|---|---|
| Deterministic calculations risk being described as AI | Medium | AI governance | Public UI and API types mix “context,” “score,” and “AI-assisted” labels |
| Human review is not always distinguished from automated calculation in public copy | Medium | AI governance / UX | Stewardship requires clarity; implementation is uneven across pages |

