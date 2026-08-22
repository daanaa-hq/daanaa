# Discovery — Org Enrichment & Link Finding

## Canonical Files

- **`discovery_daemon.py`** — Continuous daemon that discovers new orgs + enriches existing ones (runs 24/7)
- **`website_discovery_comprehensive.py`** — Website extraction pipeline (scrapes websites for info, donation links, etc.)
- **`charity_navigator_verify.py`** — Uses official Charity Navigator API to find websites + verify orgs

## Enrichment Phases

The discovery_daemon coordinates:

1. **Phase 1: Website Discovery** — Find .org sites for 113K orgs
   - Uses Charity Navigator official API
   - Falls back to web search if CN fails
   - Verifies domain ownership (WHOIS check)

2. **Phase 2: Link Extraction** — Scrape donate URLs, mission, leadership
   - Async scraping (8 workers)
   - Confidence scoring (0-100, logged)
   - Retry on transient failures

3. **Phase 3: Enrichment** — Vectorization, cause tagging, FTS index
   - Embeddings via mxbai-embed (local llama.cpp)
   - Cause tag extraction (AI generation via Qwen)
   - FTS search index rebuild

## How To...

**Monitor discovery daemon:**
```bash
tail -f logs/discovery_daemon.log
# Or check health:
python3 -c "import sqlite3; conn = sqlite3.connect('data/merit_registry.db'); count = conn.execute('SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL').fetchone()[0]; print(f'Orgs with websites: {count:,}')"
```

**Force discovery on a single org:**
```bash
python3 -c "
from scripts.discovery.discovery_daemon import discover_single_org
discover_single_org('<EIN>')
"
```

**Check website discovery status:**
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('data/merit_registry.db')
stats = conn.execute('''
  SELECT
    COUNT(*) as total,
    SUM(CASE WHEN website IS NOT NULL THEN 1 ELSE 0 END) as with_website,
    SUM(CASE WHEN donate_url IS NOT NULL THEN 1 ELSE 0 END) as with_donate_url
  FROM registry_enriched
''').fetchone()
total, with_web, with_donate = stats
print(f"Total orgs: {total:,}")
print(f"With websites: {with_web:,} ({100*with_web/total:.1f}%)")
print(f"With donate URLs: {with_donate:,} ({100*with_donate/total:.1f}%)")
EOF
```

## Supporting Scripts

- `../check_link_health.py` — Verify donation and website URLs are still valid
- `../migrations/backfill_flame_websites.py` — Bulk website backfill from an external source
- Other superseded discovery utilities are not canonical.

## Rate Limiting & Ethics

- Respects robots.txt + Crawl-Delay headers
- No User-Agent spoofing (honest scraping)
- Backoff on 429 (too many requests)
- 2s delay between requests to same domain
- See DECISIONS.md 2026-07-18 ("Crawler Etiquette")

## Do Not Use

- Superseded website scrapers that are not named above
- `legacy_website_discovery_*.py` (superseded by comprehensive version)
- Direct WHOIS queries without fallback (Charity Navigator API is canonical)

## Database Schema

**Input:** `registry_enriched` (EIN, org_name, location)
**Output:** Updated columns:
- `website` — Verified .org domain
- `website_status` — HTTP status of last check
- `website_final_domain` — Canonical domain after redirects
- `donate_url` — Verified donation link
- `donate_confidence` — 0-100 confidence score

## Recent Changes

- 2026-08-12: Task #2 cause synonym expansion (improves search relevance for discovered orgs)
- 2026-07-25: Discovery daemon restarted, now 24/7 operation
- 2026-07-24: Fixed FTS sync drift (298K orgs weren't indexed)
- 2026-07-18: Crawler etiquette decision (use robots.txt, respect Crawl-Delay)

## Troubleshooting

**Discovery daemon not running?**
→ Check: `systemctl status discovery_daemon` or `ps aux | grep discovery_daemon`
→ Restart: `systemctl restart discovery_daemon`
→ Logs: `tail -f logs/discovery_daemon.log`

**Website not found for org?**
→ Run manual discovery: `python3 -c "from scripts.discovery.discovery_daemon import discover_single_org; discover_single_org('<EIN>')"`
→ Check Charity Navigator API directly (may be timeout)
→ Add to manual backfill queue (talk to Akbar)

**Donation link broken?**
→ Run link health check: `python3 scripts/check_link_health.py`
→ Disable link if 404 (set donate_url = NULL, donate_confidence = 0)

## See Also

- `docs/projects/discovery/WEB_DISCOVERY_PIPELINE.md` — Website-discovery pipeline notes
- `docs/ENRICHMENT_RUNBOOK.md` — Enrichment operating notes
- DECISIONS.md 2026-07-18 — Crawler etiquette policy
