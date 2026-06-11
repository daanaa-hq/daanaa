# Daanaa API v5.0 Response Format

## Overview

The v5.0 API returns enriched organization data with peer-relative financial context, calculated against 15 scoring groups (5 archetypes × 3 revenue bands).

## Organization Detail Response

Each org detail response includes:

```json
{
  "ein": "123456789",
  "name": "Example Healthcare Clinic",
  "ntee1": "C",
  "revenue": 287000,
  
  "merit_score": 42,
  "merit_archetype": "Donation-Funded Programs",
  "merit_archetype_key": "donation_funded",
  "merit_band": "Professional ($150K–$700K)",
  "merit_band_key": "professional",
  
  "peer_group_label": "Donation-Funded Programs, Professional ($150K–$700K)",
  "peer_org_count": 77000,
  
  "financial_context": {
    "reserves_months": 9.2,
    "reserves_p25": 7.2,
    "reserves_p50": 11.0,
    "reserves_p75": 16.2,
    "reserves_percentile": 30,
    
    "labor_pct": 8.0,
    "labor_p50": 15,
    
    "health_signal": "CAUTION",
    "healthy_rate_peer": 51
  },
  
  "donor_copy": "This organization is a Donation-Funded Programs nonprofit with a budget in the Professional ($150K–$700K) range. Looking at its financial stability: Most organizations like this one keep about 11 months of operating costs in reserve. This one has 9.2 months. That's below the typical level for similar organizations. Worth understanding before you give. This comparison is based on public IRS 990 data from 77,000 similar organizations."
}
```

## Field Descriptions

### Identity Fields
- **ein** (string): Employer Identification Number (9 digits)
- **name** (string): Organization legal name
- **ntee1** (string): IRS NTEE category (single letter, A–Z)
- **revenue** (number): Total annual revenue in dollars

### Scoring Fields
- **merit_score** (number): Percentile rank within peer group (0–99)
  - Deprecated field (kept for backwards compatibility)
  - New scoring is peer-relative; see `financial_context.reserves_percentile`
  
- **merit_archetype** (string): Financial operating model
  - "Donation-Funded Programs" (52% of sector)
  - "Fee-for-Service Operators" (37% of sector)
  - "Endowment-Funded Grantmakers" (9% of sector)
  - "Membership Dues Organizations" (1% of sector)
  - "Mutual-Benefit Payers" (1% of sector)
  
- **merit_archetype_key** (string): Archetype identifier for programmatic use
  - "donation_funded", "fee_for_service", "endowment", "membership", "mutual_benefit"
  
- **merit_band** (string): Revenue size band
  - "Micro (<$150K)"
  - "Professional ($150K–$700K)"
  - "Established (>$700K)"
  
- **merit_band_key** (string): Band identifier
  - "micro", "professional", "established"

### Peer Group Fields
- **peer_group_label** (string): Human-readable peer group description
  - Example: "Donation-Funded Programs, Professional ($150K–$700K)"
  
- **peer_org_count** (integer): Number of orgs in peer group (sample size for benchmarks)

### Financial Context
- **reserves_months** (number): Months of operating costs in reserves
- **reserves_p25, reserves_p50, reserves_p75** (number): Percentile benchmarks for peer group
- **reserves_percentile** (number): This org's percentile rank (0–99)
  - "This org's reserves rank at the 30th percentile within its peer group"
  - Meaning: 30% of similar orgs have lower reserves; 70% have higher

- **labor_pct** (number): Percentage of budget spent on labor/salary
- **labor_p50** (number): Median labor % for peer group

- **health_signal** (string): Funding signal relative to peer median
  - "HEALTHY" — reserves ≥ p75
  - "STABLE" — reserves between p25 and p75
  - "CAUTION" — reserves < p25
  
- **healthy_rate_peer** (number): Percentage of peer group at "HEALTHY" level
  - Used to contextualize this org's health within the group

### Donor-Facing Copy
- **donor_copy** (string): Complete paragraph explaining the org's financial position in non-technical language
  - Safe for direct display to donors
  - Based on reserves comparison to peer median
  - Includes note that comparison is peer-based
  - References peer group size and IRS data source

## HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Org found and scored |
| 404 | EIN not found in registry |
| 400 | Invalid EIN format |
| 500 | Scoring error (rare; scoring is deterministic) |

## Example Use Cases

### Display on org detail page

```javascript
// Fetch org data
const org = await fetch(`/api/orgs/${ein}`).then(r => r.json());

// Display archetype + band
console.log(`${org.merit_archetype} | ${org.merit_band}`);

// Display financial health
console.log(`Reserves: ${org.financial_context.reserves_months} months`);
console.log(`Peer median: ${org.financial_context.reserves_p50} months`);
console.log(`Your percentile: ${org.financial_context.reserves_percentile}th`);

// Display donor-ready text
console.log(org.donor_copy);
```

### Peer comparison in search results

```javascript
// Show archetype badge
<span class="archetype">{org.merit_archetype}</span>

// Show health signal
<span class="health-signal">{org.financial_context.health_signal}</span>

// Show peer group size
<p>Compared to {org.peer_org_count.toLocaleString()} similar organizations</p>
```

### Filtering by peer group

```javascript
// Find all "Donation-Funded Professional" orgs
const filter = {
  merit_archetype_key: "donation_funded",
  merit_band_key: "professional"
}
```

## Backwards Compatibility

The v4.0 `merit_score` field is still present but **deprecated**. New applications should use `financial_context.reserves_percentile` instead.

The old field represented absolute financial health (0–100 scale with thirds). The new field represents peer-relative position (percentile rank 0–99 within peer group).

## Notes on Accuracy

- Scores are deterministic from IRS 990 data.
- Benchmarks are updated monthly as new IRS data becomes available.
- ~98% of orgs are successfully assigned to a valid peer group.
- ~2% of orgs lack sufficient financial data and cannot be scored.
- Peer groups have minimum n=174 (smallest group: Membership Micro); most groups have n≥1,000.

## Methodology

See `/methodology` for the full peer grouping logic and benchmarking approach.
