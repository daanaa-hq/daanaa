# Lessons from the Best Search Engines — Applied to Daanaa

Researched 2026-07-18 alongside the search overhaul (task #18). Each lesson is
mapped to what Daanaa already does, what we adopted today, and what remains on
the roadmap. Privacy adaptations are explicit: several industry practices
(per-user click models, personalization) conflict with Stewardship P2 and are
deliberately adapted or rejected, not copied.

---

## Lesson 1 (Google): Understand intent BEFORE ranking

Google's pipeline separates query understanding (what is this person looking
for?) from ranking (which page best serves it). Query classes are scored
differently — a navigational query ("american red cross") and an exploratory
query ("help kids read") need different machinery.

**Daanaa status: partially adopted, and today's work extended it.**
- Already: EIN-looking queries route to EIN lookup; zip codes intercept to
  location; noise words strip.
- Today: exact typed-name matches pin first — a navigational query now behaves
  navigationally instead of drowning in bm25 neighbors.
- Roadmap: classify name-shaped vs cause-shaped queries explicitly. Name-shaped
  ("st judes memphis") → name+location machinery; cause-shaped ("help kids
  read") → lean on semantic/synonym path earlier instead of as fallback.

## Lesson 2 (Algolia): Rank by a transparent tie-breaking cascade, not one opaque score

Algolia's core insight: instead of blending signals into a single magic number,
apply ordered criteria — typo count, then words matched, then proximity, then
attribute importance, then position, then exact match. Each step only breaks
ties from the previous one. The result is explainable: you can say exactly WHY
result A beat result B.

**Daanaa status: adopted the pattern today; extend deliberately.**
- Today's ordering IS a two-step cascade: exact-typed-name → bm25 (which
  itself weights org_name 10, mission 5 via `bm25(org_fts, 10, 5, 1, 1)`).
- The cascade pattern fits Daanaa's P9 (explainable decisions) far better than
  a learned blended score would. Candidate next tiers, in order: all-words-
  matched before some-words-matched; name-starts-with-query before name-
  contains-query. Never a merit/size tier in the cascade (P7).

## Lesson 3 (Algolia): Typo tolerance is table stakes — with first-letter asymmetry

Algolia tolerates up to 2 typos per word, counts a first-letter typo double
(people rarely mistype the first character), and ranks exact matches above
typo-corrected matches so tolerance never pollutes precision.

**Daanaa status: gap — this is our biggest remaining findability lever.**
- FTS5 has no native fuzzy matching. Today's prefix queries (`"jude"*`) catch
  suffix variance ("JUDES") but not internal typos ("st judse").
- Roadmap (in order of cost/benefit):
  1. Spellfix-style candidate generation ONLY when a query yields 0-5 results
     (SQLite `spellfix1` extension, or trigram LIKE fallback — local, no cost).
  2. Rank corrected matches BELOW uncorrected ones (Algolia's rule), and label
     them honestly: "Showing results for st jude" (P3: say what we did).
  3. First-letter-anchored correction first (cheapest, highest precision).

## Lesson 4 (industry-wide): Measure with golden queries + zero-result mining

Every serious search team maintains (a) a golden set of queries with known
correct results, run as regression tests, and (b) systematic mining of queries
that returned nothing — the most honest signal of unmet demand that exists.

**Daanaa status: adopted today.**
- `tests/test_search_quality.py` is the golden set (43 tests, hostile queries +
  findability, both backends); `/search-quality` skill is the audit runbook.
- Zero-result queries now log server-side to `analytics_zero_result_queries`
  with mode `fts_server`. Review cadence: check top zero-result patterns in the
  weekly audit; each cluster is either a synonym gap, a noise-word gap, a typo
  pattern, or genuinely missing data.

## Lesson 5 (Google — ADAPTED for privacy): Behavioral feedback improves ranking

Google's ranking is heavily informed by aggregated interaction data — clicks,
dwell, reformulations — interpreted through click models that separate signal
from noise.

**Daanaa status: adopt ONLY the aggregate form. The per-user form is rejected.**
- P2 prohibits tracking donor behavior into profiles. No per-user click logs,
  no personalization, no dwell tracking. This is a deliberate rejection, not a
  gap — write it down so growth pressure never "rediscovers" click tracking.
- What IS permitted and useful: the aggregate, anonymous counters we already
  keep (`analytics_search` term counts, zero-result queries, Plausible
  pageviews). Reformulation patterns can be inferred in aggregate (same-day
  term pairs) without any user identity. Use these to tune synonyms and noise
  words — never to reorder results per person.

## Lesson 6 (Algolia): Speed is a relevance feature

Algolia's founding bet: results-as-you-type (<50ms) changes search from a
command into a conversation. Users reformulate freely when iteration is free.

**Daanaa status: healthy, keep the SLO honest.**
- Measured today: p50 54ms, p95 245ms on the new relevance-ordered plan
  (local). The droplet has its own speed-pass architecture (bounded candidate
  sets, capped counts) from 2026-07-16.
- Rule adopted: any future ranking-cascade tier must be measured against the
  p95 < 500ms bar before shipping. A smarter slow search loses to a dumber
  fast one.

## Lesson 7 (Google): Authority signals — the part we must NOT copy

Google ranks by E-E-A-T (experience, expertise, authority, trust) — inferred
heavily from who links to whom. For nonprofits this would systematically favor
large, digitally mature, well-connected orgs.

**Daanaa status: structurally rejected (P4).**
- Popularity/backlink authority in the cascade would be a hidden penalty on
  small orgs — precisely what the peer-context system exists to avoid. Trust
  at Daanaa comes from evidence (IRS data, verified links), displayed WITH the
  result, never as a rank multiplier.

## Lesson 8 (Elasticsearch/Meilisearch): Relevance is a product surface, owned and versioned

Mature teams treat ranking configuration as versioned, reviewed product code
with regression suites — not a tuning knob twiddled in production.

**Daanaa status: adopted today.**
- Ranking behavior is now pinned by tests, changes route through DECISIONS.md,
  and the bm25 weights + cascade live in code with comments explaining each
  choice. Any weight change must run the golden set and the statistical
  validator before shipping.

---

## Priority roadmap distilled from the above

| # | Item | Lesson | Cost | Status |
|---|------|--------|------|--------|
| 1 | Exact-name pin + relevance order | 1, 2 | done | ✅ shipped 2026-07-18 |
| 2 | Golden set + zero-result mining | 4 | done | ✅ shipped 2026-07-18 |
| 3 | Typo fallback on 0-5 results (spellfix/trigram, labeled) | 3 | ~half day, local | next |
| 4 | Cause-vs-name query classification → earlier semantic path | 1 | ~1 day, local | next |
| 5 | Aggregate reformulation mining → synonym tuning | 5 | recurring, weekly audit | ongoing |
| 6 | Cascade tier: all-words-matched, name-starts-with | 2 | small, needs latency check | later |

Sources: [Google — How results are ranked](https://www.google.com/intl/en_us/search/howsearchworks/how-search-works/ranking-results/) ·
[Google ranking systems guide](https://developers.google.com/search/docs/appearance/ranking-systems-guide) ·
[How Google Search ranking works (Search Engine Land)](https://searchengineland.com/how-google-search-ranking-works-445141) ·
[Algolia — textual relevance engine](https://www.algolia.com/blog/engineering/inside-the-algolia-enginepart-4-textual-relevance) ·
[Algolia — typo tolerance](https://www.algolia.com/doc/guides/managing-results/optimize-search-results/typo-tolerance) ·
[Algolia — relevance tips](https://www.algolia.com/blog/product/algolias-top-10-tips-to-achieve-greatly-relevant-search-results) ·
[Elastic — what is search relevance](https://www.elastic.co/what-is/search-relevance) ·
[Meilisearch — search relevance](https://www.meilisearch.com/blog/search-relevance)
