# Website Discovery Integration — Live 2026-07-17 13:20+

## What Just Started

**Goal:** Website discovery drives everything. Each new website unlocks missions, cause tags, donation links, volunteer links.

### Pipeline Activated (Sequential)

1. **extract_990_fields.py** (completed once, can repeat)
   - 49K 990 XMLs scanned
   - 6,471 new websites loaded (from IRS e-file data)
   - 4,897 new missions extracted
   - Result: +1.2% website coverage

2. **web_finder_agent.py** (running now, 10K orgs, high-revenue priority)
   - Guesses domain patterns from org names
   - Verifies ownership via mxbai embeddings + name-token match
   - Target: 1–5K verified websites in next 2–4 hours
   - Fallback: Charity Navigator for high-value orgs

3. **discovery_daemon.py** (24/7 listening)
   - Wakes on each new website added
   - Extracts donation links, volunteer links, GitHub repos
   - Queues verified links for deployment

4. **overnight_pipeline.py** (runs 02:30 Central nightly)
   - Caches HTML from all discovered websites
   - Generates missions via LLM from cached content
   - Extracts cause tags (AI categorization)
   - Groups into cohorts by cause + financial metrics

### Resource Utilization (Current)

| Resource | Use | Headroom |
|----------|-----|----------|
| Embed server (11436) | web_finder domain verification | Available for queries |
| LLM server (11437, Qwen) | tomorrow 02:30 mission generation | Available now |
| Discovery daemon | Link extraction (web pages) | Can run 100 concurrent threads |
| CPU | web_finder (domain guessing) | ~30% utilized |
| Network | HTTP fetches (domain verification) | Moderate; rate-limited |

### Next 48h Milestones

- **13:30 - 18:00:** web_finder finds ~1–5K new websites (embed verification)
- **18:00 - 02:30:** discovery daemon extracts links from newly-found websites
- **02:30 - 04:30:** overnight pipeline generates missions + cause tags from all 111K+ websites
- **By 2026-07-18 09:00:** Full synergy live — every website feeds into all downstream features

---

## User Q: Charity Navigator Verification (Legal)

**Goal:** Verify low-confidence donation links against Charity Navigator (CN) data.

**Current state:** We fallback to CN when our discovery fails (89.5% coverage); CN has ~9K nonprofit profiles verified by hand.

**Legal approach (no scraping):**

1. **CN API (rate-limited, public)**: Use their HTTP API if documented (check their terms)
2. **Our existing CN cache**: We already have ~9K CN donation links in the DB (see: donate_source='charity_navigator')
3. **Cross-check vs. our DB:** For orgs we mark as low-confidence (<70), check if CN has verified data

**Safe implementation:**
- Respect robots.txt
- Use identified User-Agent (Daanaa Bot, contact: hello@daanaa.org)
- Rate limit: 1–2 req/sec (non-aggressive)
- Cache results 30 days (don't re-query immediately)

**Should we add this to web_finder_agent.py?** Yes — for orgs without any donate link, if CN has verified data, use it as fallback (disclosed as charity_navigator source).

---

## Yes to Both Questions

**Resource utilization improvement:** The pipeline now runs:
- 24/7 daemon (already running)
- Continuous web_finder (started)
- Nightly orchestrator (scheduled)
- All in parallel, no conflicts

**Charity Navigator legal verification:** Add to web_finder as fallback tier (disclosed source).

