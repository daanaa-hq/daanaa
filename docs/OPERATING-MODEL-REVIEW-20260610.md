# Operating Model Review — June 2026
**Trigger:** Leslie feedback — subcategory alignment review  
**Scope:** All 9 operating models, 766 NTEECC subcategories with ≥20 scored orgs, 407K orgs  
**Method:** Financial fingerprint analysis (program%, reserve months, log revenue) + K-means clustering  
**Status:** Research complete — proposed revisions below

---

## Current Model Summary (live v4.0)

| Model | Letters | n (scored) | prog% median | reserve median | Revenue median |
|---|---|---|---|---|---|
| Activity_Programming | A, B, N | 127,585 | 75.5% | 14.0 mo | — |
| Clinical_Reimbursement | E, F, G, H | 41,474 | 80.6% | 11.8 mo | — |
| Community_Human_Services | O, P, S | 86,298 | 76.8% | 12.1 mo | — |
| Cause_Advocacy_Research | C, D, Q, R, U, V | 32,684 | 75.6% | 13.7 mo | — |
| Direct_Delivery | I, J, L | 37,956 | 81.5% | 14.3 mo | — |
| Emergency_Logistics | K, M | 17,222 | 77.8% | 27.0 mo | — |
| Faith_Community | X | 21,816 | 70.0% | 11.3 mo | — |
| Intermediary_Public_Benefit | T, W | 30,601 | 74.2% | 22.5 mo | — |
| Membership_Mutual_Benefit | Y, Z | 11,985 | 40.4% | 34.6 mo | — |

---

## Critical Issues Found

### Issue 1 — Wrong NTEE code in Faith_Community (HIGH)
**X ≠ Faith Communities.** NTEE X = Mutual/Membership Benefit Organizations (fraternal societies, voluntary employee benefit associations, co-ops). Faith communities are NTEE W (Religion-Related), which is currently in Intermediary_Public_Benefit.

Within X, massive subcategory heterogeneity:
- X20 (Fraternal societies, 10,722 orgs): 65.8% prog, 9.8 mo reserve → looks like Community_Human_Services
- X40 (Employee benefit assoc., 483 orgs): 76.0% prog, 38.4 mo reserve
- X50 (Cooperative utilities/benefit funds, 623 orgs): **29.9% prog, 56.4 mo reserve** → clearly Membership_Mutual_Benefit
- X70 (300 orgs): 53.8% prog, 63.5 mo reserve → benefit fund pattern

**Action:** X belongs in Membership_Mutual_Benefit. W (actual religious/faith infrastructure) needs its own model.

---

### Issue 2 — W30 congregations misplaced (HIGH)
**W30 = Protestant Christian congregations (7,338 orgs, 16.9% prog, 22.2 mo reserve)**  
Currently in Intermediary_Public_Benefit alongside T (Grantmakers). A congregation does not operate like a community foundation.

Other W subcats also split:
- W80 (87.6% prog, 23.3 mo, $791K) — religious schools/hospitals operating as direct service
- W61 (70.5% prog, 29.3 mo, $3.98M) — large religious institutions  
- W30 (16.9% prog, 22.2 mo) — pure congregations (giving/tithing income, community ministry)
- W12, W033 (34-39% prog) — near Membership_Mutual_Benefit

**Action:** Create distinct Faith_Community model from W subcats that match the congregational fingerprint (W30, W33 family). W orgs with high program ratios stay in their functional model.

---

### Issue 3 — Y (Unknown/Unclassifiable) is noise in Membership_Mutual_Benefit (HIGH)
Y orgs have near-random financial behavior (IQR 85-100% in every subcategory). Subcategories within Y span every model:
- Y20 (1,249 orgs, 79.5% prog, 13.6 mo) → nearest: Clinical_Reimbursement
- Y24 (39 orgs, 84.9% prog, 13.0 mo) → nearest: Direct_Delivery  
- Y43 (1,749 orgs, 50.4% prog, 20.4 mo, $13.7M) → looks like a benefit fund
- Y30 (44 orgs, 77.9% prog, **83.6 mo** reserve) → benefit society

Y has no consistent operating model — we're benchmarking unknown orgs against each other, which is meaningless peer comparison.

**Action:** Remove Y from Membership_Mutual_Benefit. Route Y orgs to a model via financial fingerprint matching (nearest centroid fallback). Flag as "estimated model" in the UI.

---

### Issue 4 — Emergency_Logistics combines two very different reserve profiles (MEDIUM)
- K (Food, Agriculture): 72.3% prog, **17.7 mo reserve**, $240K revenue — ongoing daily food delivery
- M (Public Safety/Disaster): 82.0% prog, **38.9 mo reserve**, $180K revenue — surge-capacity disaster response

Reserve spread: 21.2 months. A food bank that operates year-round is benchmarked against a disaster relief org that holds 3 years of reserves "just in case." These have legitimately different financial health benchmarks.

Specific subcats pulling in opposite directions:
- K31 (Food banks, 1,383 orgs): 90.8% prog, 14.3 mo — textbook Direct_Delivery
- M112 (Disaster preparedness, 65 orgs): 72.6% prog, 65.2 mo — true Emergency_Logistics
- K28 (2,198 orgs): 42.8% prog, 29.4 mo → nearest: Membership_Mutual_Benefit (agricultural co-ops?)

**Action:** Consider split — Food_Nutrition (K) + Emergency_Preparedness (M). Or at minimum, separate revenue bands per sub-letter within the model.

---

### Issue 5 — S (Community Improvement) splits across two operating behaviors (MEDIUM)
- S direct service orgs (S11, S12, S99): 73-78% prog, 19-30 mo — similar to Community_Human_Services P
- S civic/membership orgs (S80, S81, S82, S47): **43-50% prog**, 20-33 mo — civic clubs, chambers, trade associations

Large misaligned subcats:
| NTEECC | n | prog% | Reserve | Description |
|---|---|---|---|---|
| S80 | 8,235 | 43.1% | 19.0 mo | Homesharing programs / civic leagues |
| S47 | 1,228 | 49.5% | 30.1 mo | Community Service clubs (Rotary, Lions) |
| S81 | 1,029 | 50.0% | 29.5 mo | Women's service clubs |
| S82 | 475 | 42.1% | 24.6 mo | Men's service clubs |
| S013 | 78 | 15.2% | 8.8 mo | Management/technical assistance (pass-through) |

Combined: ~11,000 civic/membership orgs in Community_Human_Services whose financial profile matches Membership_Mutual_Benefit, not human services delivery.

**Action:** Move S80/S81/S82/S47 family to Membership_Mutual_Benefit.

---

### Issue 6 — T (Philanthropy/Grantmaking) poorly paired with W (MEDIUM)
T = Grantmakers, DAFs, community foundations: 80.4% prog, 29.1 mo reserve  
W = Religion support infrastructure: 62.0% prog, 21.1 mo reserve  
18.4pp program spread. These are paired in Intermediary_Public_Benefit but have distinct financial fingerprints.

T operates like a Foundations model (deploys grants, holds endowments). W operates more like Community_Human_Services (direct community support, lower reserves).

**Action:** T → separate Philanthropy_Grantmaking model. W → split by congregational vs institutional (see Issue 2).

---

### Issue 7 — B94 (PTAs) in Activity_Programming (LOW)
B94 = Parent-Teacher Groups (5,775 orgs): **12.6% prog, 11.6 mo reserve, $59K revenue**  
These are fundraising vehicles (pass-through to schools) — not educational programming. Nearest model: Membership_Mutual_Benefit.

If we're benchmarking B94 on program ratio, they'll always appear "weak" vs. actual tutoring/enrichment orgs in B. Separating them improves the accuracy of both groups.

---

## K-Means Clustering (Data-Driven View)

Running k-means on 407K orgs with 4 features (prog%, reserve, log_rev, asset_ratio) at k=9–12 consistently finds these natural groups:

| Cluster Fingerprint | prog% | reserve | Revenue | Natural NTEE concentration |
|---|---|---|---|---|
| High-prog, low-reserve, large | ~87% | 3-5 mo | $200K | N, B, A, P, S (active service delivery) |
| High-prog, very-high-reserve | ~87-89% | 120 mo | $90-210K | B, A, T (endowed/foundation-backed) |
| High-prog, mid-reserve, medium | ~86% | 26-30 mo | $150-165K | B, N, S, A |
| High-prog, low-reserve, large-revenue | ~86% | 8-10 mo | $14M+ | E, B, P, F (large institutions) |
| High-prog, medium-reserve, broad | ~85% | 10-11 mo | $1.2M | P, B, S, A |
| High-prog, very-high-reserve, medium | ~81% | 96-103 mo | $1.3M | B, A, T, E (reserve-rich) |
| Near-zero prog, low reserve | ~7% | 13-14 mo | $820-870K | S, J, N (civic/membership clubs) |
| Zero prog, mid reserve | 0% | 22-24 mo | $60-63K | Dormant/data-incomplete orgs |
| Zero prog, low reserve | 0% | 3-4 mo | $80-82K | X (mutual benefit), orgs with no prog reported |
| Zero prog, very-high reserve | 0% | 120 mo | $40-60K | B, Y, A (asset-holding, no program exp) |

**Key observation:** The clustering does NOT naturally recreate the 9 current NTEE-based models. It finds **financial behavior clusters that cut across sector lines** — a food bank and a job training program look the same financially, even though they're in different NTEE categories.

This suggests the operating model taxonomy serves two purposes simultaneously (sector identity + financial benchmarking) and the tension between them is real. The proposed revision below tries to honor both.

---

## Proposed Revised Operating Models (v4.1 Draft)

| Model | NTEE Letters | Change from v4.0 |
|---|---|---|
| **Clinical_Reimbursement** | E, F, G, H | No change |
| **Direct_Delivery** | I, J, L, K31 (food banks) | Move K31 from Emergency_Logistics |
| **Activity_Programming** | A, N, B (excl. B94) | Remove B94 PTAs |
| **Community_Human_Services** | O, P, S (excl. S80/81/82/47) | Remove civic/membership S subcats |
| **Emergency_Preparedness** | M, K (excl. K31, K28) | Rename; extract food banks; remove ag co-ops |
| **Cause_Advocacy_Research** | C, D, Q, R, U, V | No change |
| **Philanthropy_Grantmaking** | T | Split T from W |
| **Faith_Community** | W (congregational subcats: W30, W33 family) | New — W30+W33 pulled from Intermediary |
| **Religious_Institutions** | W (institutional subcats: W61, W80, W05) | New — high-program W orgs |
| **Membership_Civic** | X, S80/81/82/47, B94, K28 | Rename from Faith_Community; absorb civic S + B94 PTAs |
| **Y_Fallback** | Y, Z | Unscored model; assign via nearest-centroid; flag in UI |

*Note: net model count goes from 9 → 11 (split Emergency into 2; split Intermediary into 3; rename Faith to reflect actual X code content). Revenue bands would be recomputed per model from live data.*

---

## Recommended Next Steps

1. **Confirm NTEE code intent with Leslie** — the W/X confusion may reflect different NTEE versions or intent misalignment in how IRS codes were mapped at ingestion.

2. **Validate B94 / S80 / K28 label accuracy** — spot-check 20 orgs from each before moving them.

3. **Implement Y fallback (nearest centroid)** — doesn't change current scoring, just ensures Y orgs get meaningful benchmarking instead of peer-comparing with each other.

4. **Recompute revenue bands** after any model reshuffling — bands are octile-derived from the model's org set; they'll shift as membership changes.

5. **A/B test with donors** — does the revised model labeling change perceived credibility? The model name shown to donors (when shown at all) should resonate with what the org actually does.

6. **Rescore all orgs** with revised model assignments — estimated ~50K orgs would change model and therefore peer cell.

---

*Research run: 2026-06-10 | DB: merit_registry.db | Scorer: v4.0 | 407K orgs, 766 NTEECC subcats*
