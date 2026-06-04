# Operating Models v4.0 — NTEE Mapping & Revenue Bands

**Purpose:** Define 8 operating models across all NTEE categories, with model-specific revenue bands for peer grouping.

**Data coverage:** 71,473 complete-fingerprint orgs (revenue + expenses + assets + net assets + reserves + program% + operating model).

---

## NTEE-to-Model Mapping

```python
OPERATING_MODELS = {
    'Direct_Service': {
        'ntee': ['B', 'C', 'P', 'F', 'T', 'I', 'U', 'Z'],
        'count': 22916,
        'description': 'Direct service delivery to individuals/communities (employment, education, animal welfare, crime prevention, social services, emergency assistance)',
    },
    'Mission_Infrastructure': {
        'ntee': ['A', 'E', 'G', 'L', 'M', 'O', 'S', 'D'],
        'count': 26413,
        'description': 'Institutions: schools, health systems, arts, libraries, museums, disease research',
    },
    'Research_Academia': {
        'ntee': ['J', 'R', 'N'],
        'count': 10729,
        'description': 'Universities, medical research, scientific bodies',
    },
    'Foundations': {
        'ntee': ['Y'],
        'count': 3266,
        'description': 'Grantmaking entities, endowments',
    },
    'Membership_Advocacy': {
        'ntee': ['X', 'V'],
        'count': 2940,
        'description': 'Member-driven organizations, voluntarism, advocacy networks',
    },
    'Religion_Spiritual': {
        'ntee': ['W'],
        'count': 3764,
        'description': 'Faith communities, spiritual organizations',
    },
    'International_Development': {
        'ntee': ['Q'],
        'count': 601,
        'description': 'Cross-border development, humanitarian aid',
    },
    'Asset_Stewards': {
        'ntee': ['K', 'H'],
        'count': 844,
        'description': 'Nursing homes, hospitals, facility stewardship',
    },
}
```

---

## Model-Specific Revenue Bands

**Each model has 8 octile-based bands in log₁₀(revenue) space, ensuring balanced peer groups (~12.5% per band).**

### Direct Service (22,916 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $27,493 | 2,865 |
| 1 | $27,493 | $51,353 | 2,864 |
| 2 | $51,353 | $75,380 | 2,865 |
| 3 | $75,380 | $112,456 | 2,865 |
| 4 | $112,456 | $176,201 | 2,863 |
| 5 | $176,201 | $368,616 | 2,865 |
| 6 | $368,616 | $1,470,577 | 2,864 |
| 7 | $1,470,577 | ∞ | 2,865 |

### Mission Infrastructure (26,413 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $27,538 | 3,302 |
| 1 | $27,538 | $55,018 | 3,302 |
| 2 | $55,018 | $81,760 | 3,301 |
| 3 | $81,760 | $116,970 | 3,301 |
| 4 | $116,970 | $170,692 | 3,302 |
| 5 | $170,692 | $277,720 | 3,302 |
| 6 | $277,720 | $687,742 | 3,301 |
| 7 | $687,742 | ∞ | 3,302 |

### Research / Academia (10,729 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $32,481 | 1,341 |
| 1 | $32,481 | $56,278 | 1,343 |
| 2 | $56,278 | $77,465 | 1,340 |
| 3 | $77,465 | $101,313 | 1,341 |
| 4 | $101,313 | $136,173 | 1,340 |
| 5 | $136,173 | $189,575 | 1,342 |
| 6 | $189,575 | $345,764 | 1,341 |
| 7 | $345,764 | ∞ | 1,341 |

### Foundations (3,266 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $23,735 | 409 |
| 1 | $23,735 | $43,760 | 408 |
| 2 | $43,760 | $64,403 | 408 |
| 3 | $64,403 | $93,374 | 408 |
| 4 | $93,374 | $146,142 | 408 |
| 5 | $146,142 | $271,438 | 408 |
| 6 | $271,438 | $692,572 | 408 |
| 7 | $692,572 | ∞ | 409 |

### Membership / Advocacy (2,940 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $34,310 | 368 |
| 1 | $34,310 | $60,506 | 367 |
| 2 | $60,506 | $89,984 | 368 |
| 3 | $89,984 | $124,164 | 367 |
| 4 | $124,164 | $176,514 | 367 |
| 5 | $176,514 | $292,835 | 368 |
| 6 | $292,835 | $696,571 | 367 |
| 7 | $696,571 | ∞ | 368 |

### Religion / Spiritual (3,764 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $20,004 | 471 |
| 1 | $20,004 | $45,205 | 470 |
| 2 | $45,205 | $70,374 | 471 |
| 3 | $70,374 | $105,577 | 470 |
| 4 | $105,577 | $154,536 | 470 |
| 5 | $154,536 | $229,829 | 471 |
| 6 | $229,829 | $419,777 | 470 |
| 7 | $419,777 | ∞ | 471 |

### International Development (601 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $20,493 | 76 |
| 1 | $20,493 | $46,060 | 74 |
| 2 | $46,060 | $78,026 | 76 |
| 3 | $78,026 | $120,445 | 75 |
| 4 | $120,445 | $178,941 | 74 |
| 5 | $178,941 | $341,100 | 76 |
| 6 | $341,100 | $1,295,575 | 75 |
| 7 | $1,295,575 | ∞ | 75 |

### Asset Stewards (844 orgs)

| Band | Low | High | Orgs |
|------|-----|------|------|
| 0 | $0 | $39,502 | 106 |
| 1 | $39,502 | $74,239 | 105 |
| 2 | $74,239 | $114,717 | 106 |
| 3 | $114,717 | $175,185 | 105 |
| 4 | $175,185 | $277,561 | 105 |
| 5 | $277,561 | $560,398 | 106 |
| 6 | $560,398 | $1,846,508 | 105 |
| 7 | $1,846,508 | ∞ | 106 |

---

## Financial Health Scale (3 tiers) — Model-Specific Meanings

Scale 2 uses percentile rank *within the (model, band) peer cell* mapped to terciles:
- **Top third:** Strong
- **Middle third:** Stable
- **Bottom third:** Inspiring

| Model | Strong | Stable | Inspiring |
|-------|--------|--------|-----------|
| Direct Service | High program efficiency, resource leverage | Predictable revenue, healthy reserves | Doing remarkable work with constraints |
| Mission Infrastructure | Reserves support stable operations | Sustained operations, steady reserves | Visionary impact despite constraints |
| Research / Academia | Well-funded pipelines, stable base | Sustained funding streams, predictable | Innovative with limited resources |
| Asset Stewards | Assets well-maintained, healthy reserves | Stable asset preservation | Growing asset base with impact |
| Foundations | Active, sustained grant deployment | Endowment stable, predictable giving | Emerging foundation, building capacity |
| International Development | Efficient cross-border delivery | Reliable operations, stable reserves | Scaling operations with vision |
| Membership / Advocacy | Healthy member-revenue base | Stable membership/advocacy revenue | Growing member base, expanding reach |
| Religion / Spiritual | Strong financial reserves, impact | Stable operations, predictable giving | Growing congregation/mission |

---

## Implementation Notes

1. **Org classification:** For each org, extract NTEE1, find matching model from OPERATING_MODELS.
2. **Revenue band:** For each org, find revenue, look up which band it falls into within its model.
3. **Peer cell:** Each (model, band) pair is a peer cell. Compute percentile rank *within that cell only*.
4. **Financial health:** Map percentile rank to tercile (0–33 = Inspiring, 33–67 = Stable, 67–100 = Strong).
5. **Visibility tier:** Computed separately from visibility scale (unchanged: Blazing/Burning Bright/Steady Flame/Growing/Just Starting).
6. **Output:** Each org gets: operating_model, revenue_band, peer_cell_size, financial_health, visibility_tier.

---

## Test Case: Aga Khan Foundation

- **NTEE1:** Q (International)
- **Total Revenue:** $64,900,000
- **Operating Model:** International_Development
- **Revenue Band:** Band 5 ($178,941 – $341,100)
- **Peer Cell Size:** 76 orgs
- **Expected Financial Health:** Likely "Strong" (it's a major international funder with robust operations)
- **Expected Visibility:** "Blazing" (well-known)
- **Combined:** "Blazing + Strong" — internationally recognized, robust financial position

