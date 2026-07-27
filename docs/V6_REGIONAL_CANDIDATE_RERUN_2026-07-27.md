# v6 Regional Candidate Audit

Generated: 2026-07-27T05:43:46.195832+00:00
Source: `/home/akbar/meritgiving/data/merit_registry.db` (read-only)

This is a local candidate simulation. It does not write the catalog or v6 ledger.

## Population

Active deductible organizations: **1,910,561**
Known revenue band: **571,728**
Revenue band unknown: **1,338,833**
Missing NTEECC: **431,002**
Missing archetype: **214,473**

## Candidate coverage

| Tier | Count | Share |
|---|---:|---:|
| `1_Direct_National` | 5,763 | 0.30% |
| `1_Direct_Regional` | 352,128 | 18.43% |
| `2_National_Inferred` | 5,804 | 0.30% |
| `2_Regional_Inferred` | 876,356 | 45.87% |
| `4_Archetype_Only` | 670,510 | 35.09% |
| **Total** | **1,910,561** | **100.00%** |

## Threshold review

- direct_limited_metric_peers: **21,959**
- direct_limited_peers: **21,959**
- insufficient_inferred_peers: **50,064**
- missing_peer_dimension: **620,446**

## Rules used

- 50 states map to Northeast, Midwest, South, or West.
- DC, territories, military/overseas, and unknown geography use national fallback.
- Revoked organizations are excluded from the population and peer groups.
- Direct revenue records use a revenue band and a band-specific peer group.
- Missing revenue records are not assigned a revenue band; their eventual display should be conditional by band.
- Missing NTEECC or archetype receives no numeric peer context.
- Tier 2 requires at least five peers and at least one scoreable reserve metric for candidate coverage; fewer than five scoreable metrics is marked limited for review.

## Scope by tier

### `1_Direct_National`
- national:District of Columbia: 4,054
- national:Military/Overseas: 10
- national:Territory/Freely Associated: 646
- national:Unknown geography: 1,053
### `1_Direct_Regional`
- regional:Midwest: 80,712
- regional:Northeast: 80,984
- regional:South: 110,411
- regional:West: 80,021
### `2_National_Inferred`
- national:District of Columbia: 3,714
- national:Territory/Freely Associated: 749
- national:Unknown geography: 1,341
### `2_Regional_Inferred`
- regional:Midwest: 181,105
- regional:Northeast: 149,262
- regional:South: 352,778
- regional:West: 193,211
### `4_Archetype_Only`
- national:District of Columbia: 5,440
- national:Military/Overseas: 156
- national:Territory/Freely Associated: 2,033
- national:Unknown geography: 4,740
- regional:Midwest: 175,751
- regional:Northeast: 118,328
- regional:South: 231,433
- regional:West: 132,629

