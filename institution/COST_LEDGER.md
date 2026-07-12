# Cost Ledger — Running Infrastructure & Service Costs

**Purpose:** Founder-visible, always-current view of every dollar the platform spends.
Per C-STW-001, every cost change is logged here BEFORE it takes effect. AI steward
updates this file with every cost-bearing decision; founder reads it, never hunts for it.

## Current Monthly Run Rate (as of 2026-07-12)

| Service | Cost/mo | Since | Purpose |
|---|---|---|---|
| DigitalOcean droplet (2GB/70GB) | $16.00 | 2026-07 (resized from $8) | Production serving |
| Cloudflare (Free plan) | $0.00 | — | DNS, edge caching (T0), DDoS protection |
| Google Drive backups | $0.00 | — | Offsite DB backups (free tier) |
| Domain daanaa.org | ~$1.00 | — | ($12/yr amortized) |
| Local inference (home server) | $0.00* | — | Qwen-32B + mxbai embeddings (*electricity only) |
| Twilio | usage-based | — | Concierge calls (pennies/min, low volume) |
| Lob | usage-based | — | Claim-verification letters (per letter) |
| **Total fixed** | **~$17/mo** | | |

## Approved-but-not-yet-spent

| Item | Est. cost/mo | Trigger |
|---|---|---|
| DigitalOcean droplet snapshots (T5) | +$2–3 | When founder provides DO token |
| Budget reserve (founder-approved, unused) | up to ~$100 | Only if a genuinely worthwhile upgrade appears; founder said "upgrade if you have to" 2026-07-12. Nothing currently needs it. |

## Rejected / avoided costs (efficiencies found)

| Item | Would have cost | Why avoided |
|---|---|---|
| PostgreSQL + Redis managed (DR-007) | $60/mo | Bounded dataset → baked-data architecture; superseded by DR-008 before spend |
| Elasticsearch | $80/mo | FTS5 sufficient at this corpus size |
| Datadog | $50/mo | External uptime monitoring free tier covers the real risk |
| AWS S3 + CloudFront CDN | ~$15–20/mo | Cloudflare free-tier edge caching does the same job ($0, verified live 2026-07-12) |
| Managed GPU inference | $60–70/mo | Home server Ryzen/R9700 handles all batch ML |

## Change Log

| Date | Change | Δ/mo | Authority |
|---|---|---|---|
| 2026-07-12 | Cloudflare edge caching enabled (free plan) | +$0 | DR-2026-07-12-008 |
| 2026-07-12 | Postgres/Redis/Elasticsearch path cancelled before spend | −$190 avoided | DR-2026-07-12-008 |
