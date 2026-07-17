# Executive Summary

## What Daanaa currently is

Daanaa is a nonprofit discovery platform built around public nonprofit records, peer-context financial interpretation, and direct hand-off to nonprofit-controlled actions. The repo shows a split between:

- A full Flask backend in [`daanaa_api.py`](/home/akbar/meritgiving/daanaa_api.py)
- A production-edge droplet backend in [`scripts/droplet_api.py`](/home/akbar/meritgiving/scripts/droplet_api.py)
- A React/Vite frontend in [`frontend/src`](/home/akbar/meritgiving/frontend/src)
- A SQLite-centered data pipeline and enrichment system in [`scripts/`](/home/akbar/meritgiving/scripts)

## Confirmed strengths

- Public nonprofit discovery is the core product, not a payment or fundraising processor. Evidence: stewardship rules in [`STEWARDSHIP.md`](/home/akbar/meritgiving/STEWARDSHIP.md) and the absence of payment SDK imports in [`tests/test_principles.py`](/home/akbar/meritgiving/tests/test_principles.py).
- Search is contract-tested and has a production-edge implementation that can fall back to precomputed detail data. Evidence: [`scripts/droplet_api.py`](/home/akbar/meritgiving/scripts/droplet_api.py), [`tests/test_search_reliability.py`](/home/akbar/meritgiving/tests/test_search_reliability.py).
- Claim flow has explicit legal attestations, phone/name/title requirements, and admin notification email. Evidence: [`tests/test_claim_flow.py`](/home/akbar/meritgiving/tests/test_claim_flow.py).
- The repo contains active language-governance concerns and tests that reject overstated payment/AI claims. Evidence: [`tests/test_ai_transparency.py`](/home/akbar/meritgiving/tests/test_ai_transparency.py), [`tests/test_principles.py`](/home/akbar/meritgiving/tests/test_principles.py).

## Main gaps

- The repository contains multiple overlapping conceptual systems for scoring, context, visibility, peer groups, and hidden gems. The code and docs do not yet show a single, clean public vocabulary.
- Several workflows are documented in scripts and tests, but not yet connected into one authoritative, end-to-end architecture map.
- Some features are clearly planned or partial rather than fully confirmed, including volunteer matching, financial transaction handling, and several AI-assisted enrichment paths.
- The production-edge droplet and the full backend have different responsibilities, but the repo still contains many cross-references that can confuse future maintainers.

## AI language and decision governance

Daanaa’s governance model is unusually explicit for a small repository:

- Stewardship principles require evidence-based trust signals, privacy by default, human accountability, and explainable decisions.
- Tests enforce some of that language technically, especially around payments, claims, security headers, and public wording.
- The current codebase still exposes a mix of deterministic calculations, AI-assisted enrichment, and human review. Those distinctions should be kept visible in public copy and internal docs.

## High-confidence architecture callouts

- Nonprofit discovery and profile rendering are supported.
- Claiming a nonprofit profile is supported.
- Search and browse are supported.
- Public browsing is filtered to exclude revoked organizations in the full backend, with a separate production-edge search contract.
- Wallet and giving-intent behavior exist, but the repo frames them as privacy-sensitive and not as money movement.

## Unverified or not found

- No confirmed payment processor integration.
- No confirmed volunteer registration lifecycle beyond discovery and submission surfaces.
- No confirmed queue system with durable dead-letter handling.
- No confirmed object-storage write path for donor/user-facing uploads in the main product flow.

