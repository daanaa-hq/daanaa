# DECISIONS.md

Append-only decision log. Each entry: **what we chose and why, plus the option
rejected.** Two lines is enough. Keeps non-obvious choices traceable
(Stewardship principle: significant decisions must be explainable).

---

## 2026-06-01 — Public web serving on a cloud droplet, not the home server
Chose a $8/mo DigitalOcean droplet to serve daanaa.org. Why: the home server sits behind
home NAT (no port forwarding) and shouldn't carry public uptime/heat. Rejected: exposing
the home Ryzen directly (NAT pain, downtime when home internet drops, security surface).

## 2026-06-01 — Lean 1.7GB web DB synced to the droplet, not the full 19GB
Chose to drop ML/pipeline tables (embeddings, raw financials, work queues) before syncing.
Why: 19GB is too slow to ship nightly and the web API never needs embeddings/raw filings.
Rejected: syncing the full DB. The home server keeps the full 19GB for the pipeline.

## 2026-06-01 — Separate daanaa_live.db via ATTACH for user-write data
Chose SQLite ATTACH + bare-name resolution so write tables live in a sync-safe DB. Why:
zero query rewrites (names resolve to the attached DB when absent from the catalog).
Rejected: prefixing 32+ queries with `live.` (error-prone, churny).

## 2026-06-01 — First-party aggregate analytics, not Plausible/Hotjar
Chose tiny first-party event counting (no cookie, no IP, no session record). Why: privacy
invariants + the 1GB droplet can't run Plausible's ClickHouse; Hotjar-style session replay
is surveillance and off-brand. Rejected: any third-party analytics or session recording.

## 2026-06-01 — Cloudflare Flexible SSL + gunicorn on :80 for beta
Chose Flexible SSL (HTTPS to visitor, HTTP Cloudflare→origin on :80). Why: simplest path
to HTTPS with no origin cert management during beta. Rejected (for now): Full(strict) with
an origin cert — REVISIT before any heavy/public launch push for true end-to-end TLS.

## 2026-06-01 — Donate paths: official sources only, or fail closed
Chose to only present a donate path as authoritative when it traces to an OFFICIAL source —
(1) the org confirmed it on claim, (2) an IRS-EIN-keyed authoritative router (Every.org,
PayPal Giving Fund), or (3) a high-confidence donate URL on the org's own verified domain.
Scraped/AI-found links stay "beta"-labeled (never authoritative); revoked/not-in-good-
standing orgs are withheld entirely. Why: protects Daanaa and donors from routing money to
wrong/fraudulent/outdated destinations; aligns with the fail-closed trust posture and
Stewardship "trust signals reflect real data." Key consequence: the EIN router is
official-by-construction (keyed on the authoritative IRS EIN, not a guessed URL), so it's
the SAFEST give path — no need to discover an invisible org's page to give them a protected
one. Rejected: presenting any high-confidence scraped link as a committed donate path.
