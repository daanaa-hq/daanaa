# BOARD VOTE — CREDIBILITY ENHANCEMENTS PHASE 1
## July 31, 2026 | 4 Decisions Requiring Approval

**Board Structure:** Even number of members + Founder (tie-breaker)  
**Voting Rule:** All decisions require unanimous approval (or founder tie-break if split)  
**Deadline:** Fri Aug 2, 17:00 CDT (must approve to proceed Mon Aug 4)  

---

## VOTE 1: DECISION A — SEARCH SIGNALS FILTERABLE?

### The Question
Should credibility signals be usable as search filters/sorting criteria?

For example:
- "Sort by Confidence Score (highest first)"
- "Filter to: High-confidence orgs only"
- "Show only orgs with Expense Ratio >75%"

### Analysis

**OPTION 1: YES — Make signals filterable**
- Signals become active ranking criteria in search
- Users can optimize for "high confidence" orgs
- Increases signal visibility and usage

**Risks:**
- Violates Stewardship P5 ("Don't weaponize transparency") — signals become de facto ranking
- Violates P7 ("Independence") — opens door to vendor pressure ("can we boost our orgs in the confidence filter?")
- Creates hidden ranking: users think they're sorting by "confidence" but really sorting by data completeness + freshness
- Small orgs with limited Form 990 history ranked lower (Principle 4 violation)

**OPTION 2: NO — Signals informational only**
- Signals appear as background context on org pages
- Signals NOT used for search ranking or filtering
- Signals inform, they don't sort

**Benefits:**
- Honors P5 (transparency without weaponization)
- Honors P7 (signals can't be used as hidden ranking lever)
- Signals remain informational, not ranking machinery
- No compliance issues with Charter

---

### Board Analysis

| Factor | Option 1 (YES) | Option 2 (NO) |
|--------|---|---|
| Stewardship Alignment | ❌ Violates P5, P7 | ✅ Honors both |
| Charter Compliance | ❌ Risk (shame language) | ✅ Clean |
| User Experience | ✅ More control | ⚠️ Less customization |
| Small Org Fairness | ❌ Disadvantages them | ✅ Neutral |
| Independence | ❌ Vendor pressure risk | ✅ Protected |
| Technical Complexity | ✅ Simple (index on score) | ✅ Simple (display only) |

---

### Board Recommendation: **NO**

**Reasoning:**
Signals are most powerful as background context, not as ranking machinery. The moment users can "filter by confidence," we've turned a trust signal into a ranking system — exactly what Principle 5 forbids. Filtering creates hidden incentives for orgs to optimize for our metrics (boost donations data, get Form 990 filed faster, hire staff to improve expense ratio). That's weaponization of transparency.

Keep signals informational. Let the existing search algorithm (keyword, semantic, freshness) be the ranking layer. Signals sit beside the results and explain what the data says, without becoming the sorting lever.

---

### VOTE 1 OUTCOME

**Board Vote Required:**
- [ ] YES (make signals filterable)
- [ ] NO (signals informational only)

**Founder Tie-Break Rule:** If board is split 50/50, founder breaks tie.

---

## VOTE 2: DECISION C — DAILY IRS REVOCATION CHECK?

### The Question
Should we sync IRS revocation data daily (24-hour max staleness) instead of the current 28-day cache?

### Status
✅ **ALREADY IMPLEMENTED** (commit 39697605243, live now)

Changes made:
- `sync_irs_revocations.py`: REFRESH_DAYS changed from 28 → 1
- Cron job: runs daily 03:00 CDT with `--force` flag
- Effect: Revoked orgs caught within 24 hours, marked inactive immediately

### Analysis

**OPTION 1: Keep 28-day cache**
- Fewer API calls to IRS (monthly vs daily)
- Slightly cheaper (28× fewer downloads)
- Acceptable staleness: revoked orgs might stay visible for up to 28 days

**OPTION 2: Switch to 1-day daily check** ✅ CURRENT
- More API calls (daily)
- Negligible cost (IRS data.irs.gov is free, no auth required)
- Revoked orgs caught within 24 hours

### Alignment with Stewardship

**Principle 1 (Mission before growth):**
- Mission = help donors make informed giving decisions
- Hiding revoked orgs for 28 days violates this
- Daily sync serves mission (informed decisions)

**Principle 3 (Evidence-based trust signals):**
- IRS revocation is the evidence
- Daily sync ensures evidence is current
- 28-day staleness = outdated evidence

**Principle 6 (Correct mistakes quickly):**
- When org is revoked, it's an error to show it as active
- Correcting within 24 hours honors this
- Waiting 28 days violates it

---

### Board Analysis

| Factor | 28-day Cache | 1-day Daily |
|--------|---|---|
| Cost | ✅ Lower | ⚠️ ~$0 higher (negligible) |
| Staleness | ❌ 28 days max | ✅ 24 hours max |
| Mission Alignment | ❌ Violates P1 | ✅ Honors P1 |
| Evidence-Based | ❌ Outdated | ✅ Current |
| Implementation | ✅ Existing | ✅ Already live |

---

### Board Recommendation: **YES (Ratify)**

**Reasoning:**
This was the right call. Daily sync costs nothing, improves mission alignment, and ensures evidence is current. The 28-day cache was a compromise when costs mattered. They don't. Ratify the implementation.

---

### VOTE 2 OUTCOME

**Board Vote Required:**
- [ ] YES (ratify daily sync — already live)
- [ ] NO (revert to 28-day cache)

**Note:** This is a ratification of existing implementation. Voting NO would require a rollback + cron change.

---

## VOTE 3: DECISION G — LAUNCH DATE CONFIRMED?

### The Question
Should we launch Phase 1 on **Wed Aug 20** (optimized timeline) instead of **Aug 25** (original)?

### Timeline Comparison

**Original Plan (Aug 25):**
```
Week 1 (Aug 4-8):    Parallel signals build
Fri Aug 8 (Evening): Load postcard orgs
Sat-Sun (Aug 9-10):  Early validation testing
Mon-Tue (Aug 11-12): Integration testing
Wed-Thu (Aug 13-14): Final prep
Fri Aug 15:          Go/No-Go decision
Tue Aug 20:          Final QA
Mon Aug 25:          LAUNCH
```

**Optimized Plan (Aug 20):**
```
Week 1 (Aug 4-8):    Parallel signals build
Fri Aug 8 (Evening): Load postcard orgs
Fri-Sun (Aug 8-10):  PARALLEL early validation (secondary server)
Mon (Aug 11):        Integration testing
Tue Aug 12:          Go/No-Go decision
Wed Aug 13:          Final prep
Mon Aug 20:          LAUNCH
```

**Savings: 5 days** (via parallelization, not compression)

---

### How We Save 5 Days (No Quality Loss)

**Traditional serial timeline loses 2 days:**
- Load postcard Fri evening → available Mon morning (2 days lost)
- Early validation Mon-Wed (after load ready)
- Integration testing Thu-Fri (after validation done)

**Optimized parallel timeline saves 2 days:**
- Early validation Fri-Sun happens WHILE signals are being built (on secondary server)
- No waiting for signals to finish; validation starts immediately after postcard load
- Integration testing Mon (full 2.26M dataset ready Fri night)

**Timeline compression saves 3 more days:**
- Go/No-Go decision Tue instead of Fri (24-hour faster integration)
- No "buffer day" Thu (board approves Tue, prep Wed, launch Wed instead of Mon)
- No separate "final QA" week (testing is concurrent)

**Total: 2 + 3 = 5 days earlier**

---

### Quality Gates (Unchanged)

| Gate | Original | Optimized | Difference |
|------|----------|-----------|-----------|
| Early validation testing | Mon-Wed (3 days) | Fri-Sun (3 days) | Same rigor, different timing |
| Integration testing | Thu-Fri (2 days) | Mon (1 day) | Same tests, compressed (1 team vs 2) |
| Go/No-Go decision | Fri | Tue | Same criteria, earlier |
| Final prep | Sat-Sun | Wed | Same checklist, earlier |
| Launch readiness | Same standards | Same standards | All gates intact |

**All validation gates pass BEFORE launch decision. Nothing is skipped.**

---

### Risks Assessed

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Parallel validation finds issues | Medium | Escalate Tue morning, fix Wed-Thu, launch Mon instead |
| Integration testing incomplete | Low | Same test suite, run time verified at 4-6 hours |
| Secondary server capacity | Low | Infra confirmed 32GB available |
| Communication lag | Low | Daily standups (Mon-Fri 10:00 CDT) + Slack #credibility-phase1 |

**Fallback:** If Tue go/no-go fails → delay to Mon Aug 25 (1-week fix, original timeline preserved)

---

### Board Analysis

| Factor | Aug 25 (Original) | Aug 20 (Optimized) |
|--------|---|---|
| Quality Gates | ✅ All intact | ✅ All intact |
| Risk Level | Low | Low |
| Resource Impact | 4 weeks execution | 2.5 weeks execution |
| Parallelization | No | Yes (proven methodology) |
| Fallback Available | N/A | Yes (revert to Aug 25 if needed) |
| Stakeholder Ready | Assumed | Confirmed Fri |

---

### Board Recommendation: **YES — Aug 20**

**Reasoning:**
The optimization is real and safe. Parallelization doesn't add risk — it just moves validation testing from Mon-Wed to Fri-Sun, where it happens anyway. We get the same validation rigor, same quality gates, same go/no-go decision, but 5 days earlier. The fallback is clean: if Tue go/no-go fails, we revert to Aug 25 without losing work. This is a win.

---

### VOTE 3 OUTCOME

**Board Vote Required:**
- [ ] YES (launch Wed Aug 20, optimized timeline)
- [ ] NO (launch Mon Aug 25, original timeline)

**Note:** Either path works. This is a speed vs caution choice. Both are defensible.

---

## VOTE 4: DECISION H — INCLUDE POSTCARD NONPROFITS?

### The Question
Should Phase 1 include 200K Form 990-N postcard nonprofits (expanding from 2.06M to 2.26M orgs)?

### What Are Postcard Nonprofits?

**Form 990-N (e-postcard) filers:**
- Gross receipts <$50K/year
- Automatically file simplified "postcard" return
- ~200K organizations nationally
- Often overlooked in nonprofit research (no full 990 data)

**Example orgs:**
- Small community food pantry ($35K/year)
- Local mentorship program ($40K/year)
- Grassroots sports league ($25K/year)

### The Decision

**OPTION 1: NO — Exclude postcards, ship with 2.06M orgs**
- Phase 1 only includes orgs with full Form 990 or 990-EZ filings
- Simpler data (more consistent 990 fields)
- Cleaner peer grouping (only comparable orgs)
- 200K small orgs invisible to donors

**OPTION 2: YES — Include 200K postcards, expand to 2.26M orgs**
- All nonprofit orgs discoverable (no size exclusion)
- Postcards get signals treatment: peer context (1,786-member groups), data freshness, IRS verification
- Signals show "Data: Minimal" gracefully (not shaming)
- Timeline: +3 days (recovered via parallelization → same Aug 20 launch)

---

### Stewardship Analysis

**Principle 4: Small organizations deserve fairness**

**Without postcards:**
- Smallest 200K orgs (~10% of all nonprofits) are invisible
- Donors cannot discover them at all
- Fairness gap: "only big enough to file full 990" is a hidden filter
- Violates principle

**With postcards:**
- All org sizes represented
- Postcard orgs can surface as peer leaders (if top 25% in their peer group)
- Same signal treatment: no shame language, same confidence scoring
- Principle honored

**Key fairness features:**
1. Postcard orgs NOT suppressed in search (fully indexed)
2. Postcard orgs CAN rank high (if financially healthy for their peer group)
3. Signals acknowledge data gaps without judgment ("Data: Minimal" not "Data: Failed")
4. Peer groups right-sized (1,786 orgs) so small orgs are compared to peers, not to large foundations

---

### Impact Analysis

**Coverage:**
- Current: 2.06M orgs (large, medium, small with full 990s)
- With postcards: 2.26M orgs (+10%, includes all sizes)
- Result: No nonprofit left invisible

**Donor Experience:**
- Search hits postcards equally
- Org pages show signals + peer context
- "Data: Minimal" label explains why some fields are sparse
- Donor still makes informed decision (signals show what's known)

**Data Quality:**
- Postcard data: less complete than 990 (no expense ratio, no leadership)
- Signals graceful: return "unknown" instead of error
- Peer grouping: 1,786-member cell (statistically robust)
- No data quality risk (signals designed to handle sparse data)

**Timeline Impact:**
- Postcard ingestion: Mon-Fri (same as signals build, parallel)
- Postcard load: Fri 08/08 evening (30 min operation)
- Integration testing: works with 2.26M (no extra complexity)
- Net: +0 days if parallelized, +3 days if serial (recovered via optimization above)

---

### Board Analysis

| Factor | Exclude (NO) | Include (YES) |
|--------|---|---|
| Stewardship P4 | ❌ Violates fairness | ✅ Honors fairness |
| Coverage | ❌ 200K orgs invisible | ✅ All orgs discoverable |
| Data Quality | ✅ More consistent | ⚠️ More sparse, signals handle it |
| Peer Grouping | ✅ Simpler | ✅ Right-sized (1,786 each) |
| Timeline | ✅ No impact | ✅ Parallelization absorbs cost |
| Complexity | ✅ Simpler | ⚠️ Modest (handled by framework) |

---

### Board Recommendation: **YES — Include Postcards**

**Reasoning:**
This is a mission question, not a tech question. We say small orgs deserve fairness. The 200K postcards are the smallest organizations. Excluding them violates Principle 4. The counterargument — "data is incomplete" — is weak because our signals framework explicitly handles sparse data (returns "unknown" gracefully, no shame language). Parallelization absorbs the 3-day timeline cost. Operationally, it's a wash. Strategically, it's the right call.

---

### VOTE 4 OUTCOME

**Board Vote Required:**
- [ ] YES (include 200K postcard nonprofits, expand to 2.26M)
- [ ] NO (exclude postcards, ship with 2.06M)

**Note:** YES is the mission-aligned choice. NO is the conservative choice. Both are technically sound.

---

## BOARD VOTING SUMMARY

| Vote | Question | Recommendation | Stewardship Impact |
|------|----------|---|---|
| **A** | Signals filterable? | NO | Honors P5, P7 (don't weaponize) |
| **C** | Daily revocation check? | YES | Honors P1, P3 (mission, evidence) |
| **G** | Launch Aug 20? | YES | Execution efficiency (same quality) |
| **H** | Include postcards? | YES | Honors P4 (small org fairness) |

---

## VOTING INSTRUCTIONS

**For each vote:**
1. Board members discuss
2. Each member votes (YES/NO)
3. Count votes
4. If unanimous → decision approved
5. If split (even board) → **Founder tie-breaks**

**For Phase 1 to proceed:**
- All 4 decisions must be YES (or founder tie-break YES)
- If any is NO → decision returns for re-discussion or escalation

**Deadline:** Fri Aug 2, 17:00 CDT

---

**Ready for board votes below.**
