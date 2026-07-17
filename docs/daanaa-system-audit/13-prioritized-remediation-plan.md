# Prioritized Remediation Plan

## Phase A: Trust and safety

1. Standardize public terminology for score, context, ranking, and peer comparison.
   - Can be completed: entirely within application code and content, with human review.
2. Add a repository-wide language check for restricted claims.
   - Can be completed: entirely within application code and tests.
3. Map every consequential decision to a human accountability path.
   - Can be completed: mostly application code, with human review.

## Phase B: Reliability

1. Add end-to-end tests for more scripts that mutate core data.
2. Make fallbacks, retries, and recovery behavior explicit for enrichment jobs.
3. Document production-edge vs full-backend contracts in one canonical place.

## Phase C: User experience

1. Clarify what “financial context” means in donor-facing copy.
2. Separate “claimed,” “verified,” “reviewed,” and “published” states in nonprofit copy.
3. Replace volunteer coming-soon ambiguity with a clearer affordance or disablement explanation.

## Phase D: Efficiency and scale

1. Reduce redundant terminology and duplicate display logic.
2. Continue tightening search and cache contracts.
3. Keep batch enrichment and precompute work behind clear scheduling and validation gates.

## AI Language and Decision Governance

1. Publish an approved terminology standard and prohibit unsupported high-risk phrases.
2. Add a decision-rights matrix for AI-assisted enrichment, scoring, claims, and public copy.
3. Add tests that fail when deterministic calculations are labeled as AI or when public copy overclaims certainty.

