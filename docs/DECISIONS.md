# Decisions Log — Daanaa 2026

**Purpose:** Record non-obvious choices, rejected alternatives, and reasoning. Updated as decisions are made.

---

| Decision | Choice | Why | Date |
|----------|--------|-----|------|
| Gate 3 baseline | Snapshot validation sufficient for gate pass | Full 72h monitoring optional; baseline confirms V6 data 100% coverage + API correctness; continuous monitoring deferred to Phase 1-4 | Aug 11 |
| Search index | Elasticsearch | Speed + filtering | Jun 18 |
| EIN validation | Fuzzy 80%+ | Balance usability + verification; agent reviews edge cases for fraud | Jun 18 |
| Email verification | Flag mismatch for review | Catch fraud without blocking small orgs (P4 fairness); agent triages in 2–5 min | Jun 18 |
| Donation link | Optional; recommend vendors Phase 4+ | Reduce friction, keep Daanaa focused on discovery not curation, P8 (no fund handling) | Jun 18 |
| Wallet sync | Batch on login | Privacy-first (P2), lightweight infrastructure, upgrade post-launch if needed | Jun 18 |
| Volunteer skills | 8 categories | Complete but not overwhelming | Jun 18 |

---

## Notes

- **Donation link decision:** Daanaa does not discover/backfill links. Nonprofits provide their own or can be recommended to vendor partners (Phase 4 vendor network). Keeps platform focused on discovery layer.
- **Email verification:** Non-domain matches go to agent review, not auto-reject. Supports P4 (fairness to small orgs with limited email infrastructure).
- **Wallet sync:** Starts local-first on launch (localStorage), batch syncs when logged into Google account. Real-time sync deferred post-launch if demand warrants.

