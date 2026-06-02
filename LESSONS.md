# LESSONS.md

Append-only engineering memory. Each entry: **symptom → root cause → rule that
prevents recurrence.** Never make the same mistake twice. Consolidate into
`CLAUDE.md` rules every ~5–10 entries.

---

## 2026-06-01 — Cloudflare 522 after enabling proxy
- **Symptom:** Site returned Cloudflare 522 ("can't reach origin") right after flipping
  the proxy on, even though the origin served fine on direct curl.
- **Root cause:** We had migrated the origin from the home server (`108.243.3.83`) to the
  droplet (`162.243.97.179`), but the Cloudflare A records still pointed at the old home
  IP. Time was lost chasing an IPv6 red herring (gunicorn bind) before checking the A record.
- **Rule:** On ANY Cloudflare 5xx, the FIRST check is "does the A record point at the
  current origin IP?" Verify origin address before touching SSL mode, IPv6, or ports.
  When migrating origins, updating the DNS A record is step one, not an afterthought.

## 2026-06-01 — Daily catalog sync would wipe all user data
- **Symptom:** Designing feedback/analytics, realized the 7am `sync_db.sh` overwrites the
  droplet's whole `merit_registry.db` from the home pipeline — which would erase every
  user-generated row (feedback, interest signals, handoffs, analytics) each morning.
- **Root cause:** Read-only catalog data and user-write data lived in one file that gets
  wholesale-replaced by sync.
- **Rule:** Never co-locate synced read-only data with user-write data in a single synced
  file. Split write-path tables into a separate DB the sync never touches.
- **Pattern that worked:** SQLite `ATTACH DATABASE '<live>' AS live` + name resolution —
  a bare table name resolves to the attached live DB *as long as it's absent from the
  catalog* (sync drops it). Zero per-query rewrites. See `merit_api.py` `LIVE_DB_PATH`.

## 2026-06-01 — Shared link showed stale MERIT branding
- **Symptom:** Sharing daanaa.org in iMessage rendered the old "MERIT / 430,000+" preview.
- **Root cause:** `og:image` is cached very aggressively by iMessage/Apple, keyed by the
  image URL. Overwriting the same `og-image.png` filename does not bust that cache.
- **Rule:** When changing a social preview image, change the FILENAME (cache-bust, e.g.
  `og-image-v2.png`), use absolute `https://` URLs in og/twitter tags, and expect the
  preview in an already-shared conversation to lag until its cache expires.
