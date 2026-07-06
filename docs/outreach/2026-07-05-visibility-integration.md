# Visibility Integration — Outreach + Marketing Stack

The new TX outreach batch (10 emails + 3 calls) doesn't exist in a silo. It's one input
to a larger visibility/marketing system already running. Here's how it all connects.

## Live visibility infrastructure (shipping now)

**Hidden Gems Directory**
- 33.9K small, financially healthy orgs live on daanaa.org/directory 
- Weekly rotation (Monday, cron-driven) → 10 fresh gems featured
- Zero query cost (static files)
- Users see them without signing in
- SEO: each gem has an org detail page with canonical URL

**LinkedIn Gem Posts** (built 2026-07-02, dormant — waiting for login)
- 2× daily (10:00, 14:00, Mon–Fri)
- Follower-ranked org selection from enriched LinkedIn data
- Generated via GPU (Qwen3-30B, port 11437)
- Each post tags the org's LinkedIn company page if found
- Pre-batched queue (7 days pre-generated nightly at 02:00)

**Bluesky Gem Posts** (built today)
- Hourly (08:00–17:00, Mon–Fri)
- Same gem content as LinkedIn (reuses post generation)
- Independent featured-log (Bluesky + LinkedIn can feature different orgs)
- Live once bsky.social account is created + app password added

**Weekly LinkedIn Carousel**
- Monday 09:00
- Rotates: hidden gems → sector insight → hidden gems → myth bust
- Full carousel PDF generated via Pillow/ReportLab

**Thursday Sector Stat Post**
- Manual text post (generated but not auto-posted)
- Cites real data from the DB: "X% of sector Y showing CAUTION reserves"

## The feedback loop: outreach → visibility → claim

### Scenario 1: Direct claim (what we're testing)
```
1. Send "claim your profile" email to org
2. Org clicks daanaa.org/org/###?ref=outreach_tx_batch
3. Org sees their profile (mission + donate link gap)
4. Org claims profile (fills in real mission, confirms donate URL)
5. We send testimonial-ask follow-up
6. Testimonial becomes evidence for OneStar later
```

### Scenario 2: Visibility-first amplification (future, once one of the 10 gets featured)
```
1. One of the 10 TX orgs claims their profile
2. They get identified as a hidden gem (small + top peer-group rank)
3. They land in the weekly gems rotation on /directory (SEO boost)
4. Their org appears in a LinkedIn or Bluesky post (their followers see it)
5. Their network reshares it (the real distribution multiplier)
6. More people find them on Daanaa + directly on their own site
7. They send us word that it helped (voluntarily)
```

This is the coverage loop that Codex flagged: the org reshare is what makes
visibility stick. Daanaa posting into a void (0 followers) doesn't move needles.

## Action items for visibility

### Immediate (needed to launch the stack)
- [ ] LinkedIn: `python3 scripts/linkedin/linkedin_poster.py --setup` (your phone, for 2FA)
- [ ] LinkedIn: `scripts/linkedin/.session/linkedin_creds.json` with username/password
- [ ] Bluesky: create daanaa.bsky.social account, grab app password, add to `scripts/linkedin/.session/bluesky_creds.json`
- [ ] Start cron: `python3 scripts/linkedin/schedule_posts.py` (runs Monday carousel, Thu stat, daily gems 10:00 + 14:00 + hourly Bluesky, nightly prebatch)

### Integration (tie outreach to visibility once the stack is live)
- [ ] When someone from the 10 claims → flag them in the DB as a hidden gem candidate
- [ ] Include their profile in the next /directory rotation if they rank high enough
- [ ] Note: org notification email script is already built and can send "we featured you today" framing

## Metrics to track (need Plausible API key)

Once `PLAUSIBLE_API_KEY` is in `.env`:

| Metric | What it tells us |
|--------|-----------------|
| Clicks on `?ref=outreach_tx_batch` links | Which emails get attention |
| Conversions to /claim/verify | Which ones actually start claiming |
| Completed claims | How many of the 10 convert (the real number) |
| Org detail page views from LinkedIn posts | Are LinkedIn posts driving traffic? |
| Org detail page views from directory rotation | Is hidden gems directory a distribution channel? |
| Claim form abandonment | Where do people drop off? |

Without the API key, we're blind — we'll know who replied and who claimed (they'll tell us), but not the in-between behavior (clicks, partial fills, etc.).

## Key insight: visibility only works with redistribution

The bottleneck is never "do they know about Daanaa?" — it's "do they feel motivated to act?"

For small nonprofits, motivation comes from their own network seeing them, not from Daanaa's audience. So:
- Posting a gem on LinkedIn without the org seeing it = wasted cycle
- Posting + notifying the org = 10x better (they reshare to their people)
- Posting + notifying + them claiming + featuring prominently on our site = compounding visibility

This is why the org notification script matters. It closes the loop from "you appeared in our post" to "here's how to benefit from that."

---

## Current state (as of 2026-07-05)

| Channel | Status | Blocker |
|---------|--------|---------|
| Hidden gems directory | ✓ Live | None |
| LinkedIn posts | Built, dormant | Login + creds |
| Bluesky posts | Built, dormant | Account creation + app password |
| Scheduler (cron) | Ready | Waiting for above |
| Org notification email | ✓ Built | None (use now) |
| TX outreach batch | ✓ Ready | User picks from clipboard or akbar@daanaa.org connects |
| Plausible tracking | Ready | API key only |
