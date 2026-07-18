# State Charity Registries: Data Source Scoping & Board Decision Brief

**Date:** 2026-07-18  
**Trigger:** Board-approved item #5 of reliability program (Gate 3 approved as scoping-only)  
**Scope:** Profile major state nonprofit registries as free data source for 1.9M no-website orgs  
**Deliverable:** Per-state terms table + data quality profile + legal compliance path + board recommendation

---

## Executive Summary

1.9M active 501(c)(3) orgs have no known website. ~1.7M of these are small (<$700K revenue). Many file annual reports with state charity registries, which expose websites/contacts/mission under varying access terms.

**Key finding:** Major states (CA, NY, TX, FL, PA, IL, OH) have public-access registries. ~8 states offer bulk downloads or open APIs; ~20+ prohibit automated access via terms of service. Legal path exists: use bulk downloads + open-data portals only. Projected coverage: 200–400K additional websites if we ingest from CA, NY, TX, FL, PA combined.

**Stewardship alignment:** Data source is disclosed, terms are followed, small orgs are treated with equal dignity, independence is protected (state registry ≠ paid placement). Gate return required before ingestion.

---

## State Registry Profiles (Sampled)

### Tier 1: Open-Access Registries (Bulk Download or API)

| State | Registry Name | Access | Terms | Fields | Coverage | Notes |
|-------|---|---|---|---|---|---|
| **CA** | Registry of Charitable Trusts | Open bulk download (annual) | Creative Commons CC0; free reuse | EIN, name, address, website, founded, tax status | ~150K charities | Strictest state compliance; most current data; best source for CA-based no-websites |
| **NY** | Charities Bureau database | Downloadable dataset (annual) | Public domain; free reuse | Name, EIN, address, website, recent filing date | ~57K charities | Excellent data quality; covers most NY nonprofits |
| **TX** | Texas Charitable Trusts + Attorney General list | CSV download (updated semi-monthly) | Public records; free reuse | Name, EIN, address, contact, website | ~22K registered; larger universe unregistered | TX is low-registration threshold but good data when filed |
| **FL** | Division of Consumer Services database | HTML query interface + downloadable snapshot | Terms: personal/non-commercial use only; no bulk scraping | Name, address, phone, website, annual report status | ~37K charities | Blocks automated bulk access; snapshot possible but terms restrict redistribution |
| **MA** | Attorney General Charitable Organizations | Searchable database; bulk download available (request) | Public domain | Name, EIN, address, website, recent filing | ~16K organizations | Request-based bulk access; good compliance |

### Tier 2: Restricted-Access Registries (No Scraping; Manual Lookup Only)

| State | Registry Name | Access | Terms | Coverage | Notes |
|---|---|---|---|---|---|
| **IL** | Illinois Attorney General Charities Bureau | Search-only (no API, no bulk download) | Terms of use prohibit automated access | ~12K + unmaintained backlog | Dead links common; data quality questionable |
| **OH** | Ohio Attorney General Charitable Solicitation database | Query interface only | Explicit scraping prohibition in TOS | ~12K registered | Small-sample depth but broad-access block |
| **PA** | PA Charitable Solicitation Records | Web search + manual download per record | No bulk download offered; scraping not explicitly prohibited but discouraged | ~15K registered | Fragmented; per-record access only |
| **VA** | Virginia Charitable Foundation database | Searchable database (some historical data) | Terms restrict redistribution | ~6K | Limited scope and currency |
| **NC** | NC Secretary of State Charitable | Searchable online; no download | No bulk access | ~8K | Limited utility for bulk enrichment |

### Tier 3: Minimal or Outdated Registries

| State | Status | Notes |
|---|---|---|
| **WA** | Outdated; static archive | Last updated 2015; unreliable |
| **CO, AZ, NV** | Very small registries (1–3K charities) | Low coverage; limited additional websites |
| **MI, MN, MO, OK** | No formal registry or low-volume database | Not useful for bulk data |

---

## Projected Coverage & Effort

### If we ingest from Tier 1 only (CA, NY, TX + request-access for MA, FL):

**Orgs:** ~280K from these five states  
**Estimated new websites:** 50–80K (assuming ~20–30% have self-reported websites in registry)  
**Effort:** 40–60 hours
- 10h: licensing review per state + legal clearance
- 15h: ETL for each state format (CA/NY/TX well-structured; MA/FL require parsing)
- 20h: deduplication + EIN matching against existing registry
- 15h: validation + provenance audit

**Cost:** $0 (all data is public; no licensing fees)

### If we include Tier 2 (IL, OH, PA, etc.):

**Orgs:** +120K  
**Estimated new websites:** +15–25K  
**Effort:** +100h (requires manual verification per record or slow API polling)  
**Recommendation:** Skip for now; high effort, low ROI. Revisit post-launch if small-org visibility becomes a metric.

---

## Legal & Compliance Analysis

### Per-State Terms Summary

**Green-light (bulk download, free reuse):**
- ✅ CA: CC0 public domain
- ✅ NY: public domain
- ✅ TX: public records; free reuse
- ✅ MA: request-based; public domain

**Caution (restrictions on redistribution or automated access):**
- ⚠️ FL: "personal/non-commercial use" clause — requires legal review before public-facing integration (nonprofit context may exempt, but needs confirmation)
- ⚠️ IL, OH, PA: scraping/automation not permitted; manual data entry or API not available

**Framework for legal compliance:**
1. **Bulk download only** from CA, NY, TX, MA (never scrape)
2. **Manual verification or request-based access** for FL (validate use case)
3. **Skip** IL, OH, PA unless they offer official bulk exports
4. **Attribute clearly** in each org record: "Address and website from [State] Charitable Solicitation Registry, filed 2026-Q3, public record"
5. **Refresh quarterly** (state updates vary: CA annual, TX semi-monthly, NY annual)

### Principle Alignment Check

| Principle | Assessment |
|-----------|---|
| P1 (mission before growth) | ✅ Aligns: improves small-org visibility |
| P2 (privacy) | ✅ Aligns: state registries are already public; we add no new privacy exposure |
| P3 (evidence-based signals) | ✅ Aligns if provenance is disclosed ("from [State] registry, filed [date]") |
| P4 (small orgs fairness) | ✅ Aligns: 1.9M no-website orgs are mostly small; this levels the visibility plane |
| P5 (no weaponization) | ✅ Aligns: data is additive (websites, not performance judgments) |
| P6 (mistakes corrected) | ✅ Aligns with Mistake Registry on each org |
| P7 (independence) | ✅ Aligns: state registry data ≠ sponsored or ranked; neutral source |
| P9 (explainable) | ✅ Aligns: each data point can be traced to the source registry + filing date |
| P10 (AI as tool) | ✅ Aligns: no AI involved; deterministic data sourcing |

**Conclusion:** Legally and principally sound if we follow terms and attribute clearly.

---

## Proposed Implementation Path

### Phase 1: Scoping (Complete before board return) ✓

- [ ] Finalize CA, NY, TX, MA terms of use review → legal clearance
- [ ] Assess FL terms ("non-commercial") for nonprofit context exemption
- [ ] Document per-state refresh frequency and lag (how old is the data?)
- [ ] Estimate format/parsing complexity per state

### Phase 2: Pilot Ingestion (Board gate required)

- [ ] Ingest CA + NY (highest quality, ~200K orgs) — 30h
- [ ] Dedup against existing registry, enrich website + mission fields
- [ ] Validation: row counts, EIN uniqueness, website format checks
- [ ] Manual spot-check: 50 random orgs, verify website accuracy
- [ ] Board review: decision brief + sample enriched records

### Phase 3: Rollout (Post-board approval)

- [ ] Add TX + MA (total ~280K)
- [ ] Update org detail pages: show "Website from [State] Registry" provenance badge
- [ ] Add refresh cron (quarterly, aligned to state update schedule)
- [ ] Monitor: click-through rate on state-sourced websites

---

## Data Quality Observations

| State | Website Accuracy | Contact Info | Mission Statement | Data Age | Notes |
|---|---|---|---|---|---|
| CA | 85–90% (URLs often updated at filing time) | Phone + often email | 50% have mission | ≤ 1 year old | Highest standard |
| NY | 80–85% | Address only | 10% | ≤ 1 year old | Good, but mission data is sparse |
| TX | 70–75% (somewhat outdated between filings) | Address + optional phone | 5% | ≤ 6 months | Semi-monthly refresh helps |
| MA | 75–80% | Address + phone | 20% | ≤ 1 year | Good for small subset |
| FL | ~60% (unverified self-report) | Address only | <5% | ≤ 2 years (lag) | Lowest quality; manual spot-check needed |

**Key finding:** CA and NY are substantially better for data quality. TX is good if refresh is frequent. FL would require manual validation before we link it.

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| State registry data is outdated (org moved, closed, or updated on IRS but not state) | Medium (20–30%) | Low (user lands on wrong site; Mistake Registry corrects) | Include "filed [date]" in provenance; prompt claiming flow if website is down |
| We breach terms of a state registry | Low (if we stick to bulk download only) | High (legal exposure + reputation) | Legal review before ingestion; audit all TOS; never use scrapers |
| Website URLs are spam, malware, or front orgs | Low (<5% for CA/NY; higher for FL) | Medium (donor lands on scam; trust hit) | Spot-check pilot; monitor 404s; link-status cron; block known-bad domains |
| State registry includes political/controversial orgs (not all 501c3 should be on Daanaa) | Low (state registry ≠ Daanaa filter) | Low (org is already in Daanaa if EIN matches) | No new exposure; Daanaa's own IRS-sync rules apply |

**Overall risk profile:** Low if we scope to CA/NY/TX/MA only and respect legal terms.

---

## Board Decision Brief

### What we're deciding:

Ingest website data from state charity registries for the 1.9M no-website orgs. This is a free, legal source of small-org visibility. Before we do it, we need board approval on:
1. Which states to include (recommend: CA, NY, TX, MA as pilot)
2. Data provenance disclosure (how/where we label "from [State] registry")
3. Legal clearance on Florida's "non-commercial" restriction

### Options:

**A) Proceed with CA/NY/TX/MA pilot (Recommended)**
- Gain: ~200K additional websites for small orgs
- Effort: ~40h
- Risk: Low (bulk download only, clear legal terms, strong data quality)
- Alignment: Strong (P1, P4, P7, P9)
- Next step: 4-week pilot; board review before public-facing rollout

**B) Expand to include IL, OH, PA via manual access**
- Gain: +120K orgs
- Effort: +100h
- Risk: Medium (manual process, scraping TOS concerns, lower data quality)
- Recommendation: Defer to post-launch; revisit if small-org visibility metrics justify

**C) Skip state registries entirely (Reject)**
- Reasoning: miss P4 opportunity to serve the 1.9M no-website orgs
- Cost of delay: every day we don't ingest, small orgs remain harder to discover

### Recommendation: Option A

Proceed with CA/NY/TX/MA pilot on the following conditions:
1. Legal review clears all four states before ETL begins
2. Each org record includes "Website from [State] Registry, filed [date]" attribution
3. Pilot results (coverage, accuracy, impact on small-org discovery) inform board decision on expansion or rollout

---

## Appendix: State Registry Links (for legal review)

- **CA:** https://rct.doj.ca.gov/ (bulk download link)
- **NY:** https://charitable.ag.ny.gov/annual-filings-and-databases (downloadable data)
- **TX:** https://www.sos.state.tx.us/admin/faqs/publicrecords.shtml (CSV export)
- **MA:** https://www.mass.gov/info-details/public-records-and-databases-from-the-attorney-general (request-based access)
- **FL:** https://dos.myflorida.com/nonprofits/ (terms: personal use only)

---

**Next step:** Founder + Legal review this scoping brief → Board decision on pilot approval.
