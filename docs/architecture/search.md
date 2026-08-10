# Daanaa Search: Query-Understanding Layer Architecture

*Phase 0 R&D sketch — v0.1. Grounded in the competitive landscape (Candid unified search Jan 2026; Charity Navigator Horizon AI / Giving Compass Nov 2025) and Daanaa's existing stack (DuckDB, FastAPI, NCCS CORE + Unified BMF joined on EIN2, hybrid local/Claude AI).*

---

## 0. The strategic frame

Natural-language intent search is now **table stakes**, not a differentiator. Horizon AI already does plain-English → ranked results. Daanaa must match it on intent parsing, then win on the four gaps incumbents cannot close without breaking their own business model:

| Gap | Why incumbents can't close it | Daanaa's move |
|-----|-------------------------------|--------------|
| **Coverage** | CN rates ~thousands; Candid's depth needs claimed/earned Seals | Rank all 432K equally; surface 990-N orgs |
| **Honesty** | Their results don't flag thin data | Four-tier label on every result card |
| **Neutrality** | Ranking leans on ratings/Seals → favors big orgs | Relevance + fairness; no revenue, no paid placement |
| **Privacy** | Recommendations imply server-side intent tracking | On-device discovery; query understanding on public data only |

**Definition of "best search" for Daanaa:** a donor reliably finds the *right small org they'd never have found elsewhere*, and trusts what they see. Not "most results," not "fanciest features."

---

## 1. The core problem

Donors search in human terms ("help homeless vets," "after-school near me"). Your data is IRS structured data (EIN, NTEE code, registered address, revenue band). The entire game is closing that gap — fairly, for all orgs, including the 406K with no mission text and the 990-N filers with no financials.

Three sub-problems, in priority order:

1. **Intent → NTEE translation** (highest leverage). "Help homeless veterans" spans P (human services), W (public benefit), L (housing), maybe O (youth). Self-reported NTEE codes are noisy.
2. **Geographic relevance** (known gap). Registered address ≠ service area. PO boxes, accountants' offices, founders' homes.
3. **Fair ranking** (the trap). With 200 matches, what's first? Never revenue. Probably not Trust Score alone (buries 990-N orgs). Relevance-to-intent first; completeness/freshness as tiebreaker.

---

## 2. Pipeline overview

```
Donor query (natural language)
        │
        ▼
┌───────────────────────┐
│ 1. QUERY UNDERSTANDING│  Claude API (public data judgment — allowed by privacy wall)
│    NL → structured     │  Cached aggressively; this is the expensive step
└───────────┬───────────┘
            │  {ntee_clusters, geo, keywords, intent_type}
            ▼
┌───────────────────────┐
│ 2. HYBRID RETRIEVAL   │  DuckDB — runs locally, fast, free
│    keyword + semantic  │  FTS over name/mission + vector over embeddings
└───────────┬───────────┘
            │  candidate set (a few hundred)
            ▼
┌───────────────────────┐
│ 3. FAIR RANKING       │  Pure Python scoring engine
│    relevance → fairness│  NO revenue input. Tier-aware.
└───────────┬───────────┘
            │  ranked results
            ▼
┌───────────────────────┐
│ 4. HONEST PRESENTATION│  Four-tier label per result card
│    + "why this showed" │  Confidence indicator
└───────────────────────┘
```

The privacy wall holds cleanly here: every stage operates on **public IRS data only**. No donor history, no wallet, no behavioral signal enters the search path. That's both a principled stance and the thing that lets you use the Claude API for stage 1 without compromise.

---

## 3. Stage 1 — Query Understanding (Claude API)

The single highest-leverage component. Input: raw query string. Output: structured search intent.

**Target output schema:**
```json
{
  "ntee_clusters": ["P20", "W30", "L41"],   // ranked, with confidence
  "geo": { "type": "near_me|city|state|national", "value": "Houston, TX" },
  "keywords": ["veterans", "homeless", "housing"],
  "intent_type": "cause | named_org | location_first",
  "exclusions": []
}
```

**Design notes:**
- Prompt Claude to return *only* JSON (no preamble, no markdown fences), then parse safely.
- Map to **NTEE clusters**, not single codes — donor intent is fuzzier than the taxonomy. Carry a confidence score per cluster (feeds your existing NTEE Confidence Scoring work).
- Detect `intent_type` early: a named-org lookup ("American Red Cross") should short-circuit to exact/fuzzy name match and skip semantic retrieval entirely. Horizon explicitly prioritizes name matches; you should too.
- **Cache hard.** The same ~500 phrasings will cover most donor queries. A query-understanding cache keyed on normalized query text turns most lookups into zero API calls. This matters for both cost and latency.

**Build-now prototype:** you can test this today against your existing NCCS+BMF join. Take 50 realistic donor queries, run them through Claude → NTEE clusters, hand-check the mapping. That labeled set becomes your evaluation harness (see §6).

---

## 4. Stage 2 — Hybrid Retrieval (DuckDB)

Mirror what Giving Compass calls "word matching + meaning matching," but built on free local infra.

**Keyword leg (full-text search):**
- DuckDB FTS extension over org name + mission text (your ~19K Full/Strong Profile orgs).
- Handles named-org lookups and exact-term matches.

**Semantic leg (vector search):**
- Pre-compute embeddings for org name + mission + NTEE description. Store as vectors in DuckDB (it supports array columns + a VSS extension for similarity).
- This is what finds "groups feeding hungry kids" → an org described as "community nutrition program" with zero keyword overlap.
- **Critical for coverage:** for the 406K Financial-Only and 5,921 Listed-Only orgs with no mission text, embed whatever you *do* have — name + NTEE label + location. They retrieve on structured match. They still surface. They're just honestly labeled when they do.

**Fusion:** combine the two legs with reciprocal rank fusion (simple, robust, no tuning weights to overfit). Produce a candidate set of a few hundred for stage 3.

---

## 5. Stage 3 — Fair Ranking (Python scoring engine)

This is where Daanaa's mission lives or dies. The ranking function is a *policy statement*, not just an algorithm.

**Inputs allowed:**
- Relevance score (from fusion, stage 2) — **primary**
- NTEE cluster confidence match
- Geographic proximity (with the service-area caveat, §7)
- Data completeness / tier — **tiebreaker only**
- Composite Freshness Score — **tiebreaker only**

**Inputs forbidden:**
- Revenue / org size (the thing every competitor ranks on)
- Trust Score as a *primary* sort key (would bury 990-N orgs → kills the mission)
- Anything resembling paid placement

**The 990-N fairness rule:** a small org with a perfect intent match must be able to rank *above* a large, well-documented org with a weaker match. If your ranking ever does the reverse on relevance ties, you've rebuilt revenue ranking with extra steps. This is the single most important invariant to test for (and it ties directly to your open Trust Score gap — resolve them together).

---

## 6. Stage 4 — Honest Presentation

Your four-tier model is a *search feature*, not just a profile feature. No competitor does this at the result level.

Each result card carries:
- **Tier label**: Full / Strong / Financial-Only / Listed-Only
- **Plain-language honesty line**: e.g. "Listed Only — IRS-registered, location confirmed, limited public data."
- **"Why this appeared"** (optional, powerful): "Matched: veterans + housing in Houston." Builds trust *in the search itself* and is a genuine differentiator — incumbents return a ranked list with no provenance.

---

## 7. Measurement — "constantly improving," made real

"Constantly improving" without measurement is just churn. Build the harness in Phase 0; it's cheap and high-value. Extend your existing **Bias Monitoring Agent** (already specced to audit search fairness) to run these every IRS sync:

**Search quality (needs a labeled query test set — build it yourself, ~100 queries):**
- **Recall@10**: for each test query, what fraction of known-relevant orgs surface in the top 10?
- **Small-org surfacing rate**: do 990-N / sub-$50K orgs appear for queries where they're genuinely relevant, or get buried?
- **Geographic diversity**: does an NTEE-cluster query return geographically spread results, or cluster on big metros?
- **Regression detection**: re-run the full set after every monthly sync. Catch when a data change silently degrades results.

**The fairness invariant test:** construct query pairs where a small org is the better intent match than a large org. Assert the small org ranks higher. If it ever doesn't, the ranking has drifted toward size bias.

None of this requires donor surveillance — it runs on public data and a self-authored test set. That's the point.

---

## 8. Known hard problems (name them, don't paper over)

- **Service area vs. registered address** — you only have the registered address. Be honest in the UI ("registered in Houston, TX") rather than implying service coverage you can't verify. A future signal could infer service area from mission text, but only for orgs that have it.
- **NTEE self-reporting noise** — codes are org-selected and often wrong/stale. The query-understanding layer mapping to *clusters* (not single codes) partially absorbs this; NTEE Confidence Scoring flags low-trust mappings.
- **Brand-new orgs, zero data** — define a fallback retrieval state so a just-registered org isn't invisible purely because it has no embeddings-worthy text. Name + location + NTEE label is the floor.
- **Church exemption invisibility** — churches may hold status without IRS registration; they won't appear. A documented limitation, not a bug.

---

## 9. Build order (Phase 0, fits the existing stack)

1. **Labeled query set** (~100 donor queries → expected relevant orgs). Do this first; everything measures against it.
2. **Query-understanding prototype** (Claude API → NTEE clusters + geo). Test against the labeled set by hand.
3. **Keyword retrieval** in DuckDB FTS over the ~19K orgs with text.
4. **Semantic retrieval** — embed all orgs (text-rich and structured-only), DuckDB VSS.
5. **Reciprocal rank fusion** + the fair ranking function (with the forbidden-inputs discipline).
6. **Measurement harness** wired into the Bias Monitoring Agent cadence.
7. **Result-card honesty layer** (tier label + "why this appeared").

Everything above runs on free local infra (DuckDB, FastAPI, Python) plus aggressively-cached Claude API calls for stage 1 only. No new infrastructure cost. Consistent with lean-by-design.
