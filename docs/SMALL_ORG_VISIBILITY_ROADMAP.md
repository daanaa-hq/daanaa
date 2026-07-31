# Small Nonprofit Visibility Roadmap

**Vision:** As we discover more information about smaller nonprofits, make them more visible through search and discovery (not by gaming rankings, but by actually knowing them better).

**Principle:** Stewardship #4 + #5 (Small org fairness + Don't weaponize)

---

## How Phase 1 Enables This

### Current State (Today)
- 460K orgs have websites (22% coverage)
- 1.6M orgs missing websites (no online presence)
- Search ranks by keyword relevance + semantic similarity
- Small orgs often invisible: no website = no indexing = no search visibility

### Phase 1 Impact
- ✅ 2,307 new websites discovered (all verified, HTTPS)
- ✅ 6 credibility signals (shows what we know about orgs)
- ✅ Completeness score reveals data gaps (mission, website, financial data)
- ✅ These signals create search advantages for transparency, not size

### Result
Small org with newly discovered website + complete data can now:
1. Appear in search (website is indexed)
2. Show "verified + complete" signals
3. Rank higher for relevant queries (keyword + semantic)
4. NOT compete on size/revenue (peer context is size-neutral)

---

## Phase 2: Giving Wallet as Discovery Engine

Wallet creates a discovery feedback loop:

```
User saves org → Wallet logs interest
↓
Aggregate: "100 users interested in [cause] in [city]"
↓
Search learns: Small org in rural area has real demand
↓
Boost visibility for relevant future searches
```

Without profiling individual users (Stewardship #2).

---

## Post-Phase 2: Search Improvements (Roadmap)

### Week 1-2: Data Quality Boost
**Goal:** Surface smaller orgs that are well-documented

**What works:**
- Sort by completeness + relevance (not just relevance)
- Example: "Food bank in Maine" 
  - Today: Top results by keyword match
  - Improved: Top 3 by match, then 3 by "complete + relevant" (shows small org with full profile)

**Cost:** 0 (reranking logic in search handler)

### Week 3-4: Wallet Signals
**Goal:** Use collective giving intent as a discovery signal

**How:**
- Track: "How many Daanaa users saved this org?"
- Use as tiebreaker: If 2 orgs match equally on keywords, show the one more users saved
- Benefit small orgs: Collective signal is MORE powerful than org size

**Cost:** 0 (already logged in wallet)

### Week 5-6: Geographic Discovery
**Goal:** Help donors find orgs near them (not headquartered nearby, but serving their community)

**How:**
- Expand org.service_area (currently used for display)
- Search improvement: "Food banks in 60614" finds all serving that zip
- Benefit: Small local orgs now compete on relevance, not national brand

**Cost:** Minimal (already have service_area data)

### Week 7-8: "Hidden Gems" Search Filter
**Goal:** Dedicated search mode for high-performing small orgs

**Formula:** 
- Small: <$5M revenue
- High-performing: Top 30% in peer group (same size + sector)
- Real impact: Have financial reserves + good expense ratios
- Result: Users can explicitly search for "small but solid" orgs

**Example query:** `q=education&size=small&sort=peer_rank`

**Cost:** 1-2 days (new search filter + UI toggle)

---

## Protecting Against Manipulation

### What We WON'T Do
- ❌ Rank by recency (new orgs get fake boost)
- ❌ Rank by donation volume (wealthy donors get disproportionate say)
- ❌ Rank by "trending" (creates viral races, not discovery)
- ❌ Suppress large orgs (they serve real communities)

### What We WILL Do
- ✅ Rank by relevance (keyword + semantic + user intent)
- ✅ Rank by transparency (completeness of data we have)
- ✅ Rank by peer performance (compared to similar-sized orgs)
- ✅ Surface hidden gems as a choice (explicit filter, not default)

---

## Measuring Success (Aug 31 Check)

| Metric | Target | How We Measure |
|--------|--------|---|
| Small org search CTR | +20% vs baseline | Analytics per org size bucket |
| Website ingestion quality | 95%+ verified | Manual spot-check 20 random |
| Hidden gems discoverability | 100 clicks/week | Plausible event tracking |
| Wallet interest distribution | Skew toward small orgs | Aggregate wallet data (anonymized) |

---

## Long-Term Vision (6-12 Months)

1. **Knowledge Graph:** 
   - Map: Small org + sector + location + mission
   - Result: "Find all food banks serving rural Iowa teaching financial literacy"

2. **Community Builder:**
   - Show: "Other donors interested in this org also support [3 related small orgs]"
   - Benefit: Donors discover clusters of aligned impact

3. **Trust Trail:**
   - Show: "This org is used by [X] nonprofits in the network"
   - Benefit: Small org visibility through relationship signals, not rankings

---

## Why This Works

**Not a rankings game:** We're not saying "small orgs are better." We're saying "as we know more about them, they become more visible."

**Aligned with mission:** Discovery is the hard problem. Transparency (signals) + giving intent (wallet) + geographic relevance = better discovery without manipulating trust.

**Defensible:** Every improvement is traceable to real data (websites, signals, user intent), not AI bias or algorithmic manipulation.

---

## Next Steps

- ✅ Phase 1: Signals reveal what we know (completeness)
- ✅ Phase 2: Wallet reveals what donors care about (intent)
- → Phase 2+: Search improvements use both signals + intent
- → Month 2: Hidden gems filter ships
- → Month 3: Geographic discovery improvements
- → Month 6: Knowledge graph exploration

---

**Keeper:** If Phase 1 works, this roadmap becomes the foundation for all discovery improvements. Small org visibility grows because they become knowable, not because we game rankings.

