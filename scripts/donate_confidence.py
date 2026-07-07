#!/usr/bin/env python3
"""
Shared donate-link confidence scoring and identity matching.

Extracted from donation_link_pipeline.py (Task 1 of the enrichment
consolidation) so the new enrichment pipeline can reuse this proven,
already-tuned logic without duplicating it. No behavior change from
the original — same factors, same weights, same identity-match algorithm.
"""
import re

# ── Identity match (no LLM) ───────────────────────────────────────────────────

_STOP_WORDS = {
    'inc', 'the', 'of', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'at', 'by',
    'corporation', 'corp', 'llc', 'ltd', 'foundation', 'association',
    'society', 'organization', 'group', 'team', 'center', 'centre',
    'church', 'ministries', 'ministry', 'services', 'service', 'fund',
}


def identity_match(org_name: str, page_text: str) -> tuple[str, float]:
    """Return (level, ratio). Levels: exact/strong/possible/weak/mismatch/unknown."""
    words     = re.findall(r'\b[a-z]+\b', org_name.lower())
    key_words = [w for w in words if w not in _STOP_WORDS and len(w) > 2][:5]
    if not key_words:
        return 'unknown', 0.0
    page_lower = page_text.lower()[:2000]
    matches    = sum(1 for w in key_words if w in page_lower)
    ratio      = matches / len(key_words)
    if ratio >= 0.8:
        return 'exact', ratio
    elif ratio >= 0.6:
        return 'strong', ratio
    elif ratio >= 0.4:
        return 'possible', ratio
    elif ratio > 0:
        return 'weak', ratio
    else:
        return 'mismatch', ratio


# ── Confidence scorer ──────────────────────────────────────────────────────────

def score_confidence(factors: dict) -> int:
    score = 0
    if factors.get('found_on_official_website'): score += 30
    if factors.get('nonprofit_name_visible'):    score += 20
    if factors.get('website_confidence_90'):     score += 15
    if factors.get('processor_recognized'):      score += 10
    if factors.get('no_suspicious_redirects'):   score += 10
    if factors.get('city_state_match'):          score +=  5
    if factors.get('branding_matches'):          score +=  5
    if factors.get('link_works'):                score +=  5
    if factors.get('ein_visible'):               score +=  5
    # Deductions
    if factors.get('generic_platform_url'):      score -= 40
    if factors.get('name_mismatch'):             score -= 40
    if factors.get('website_not_official'):      score -= 30
    if factors.get('not_from_official_site'):    score -= 25
    if factors.get('city_state_mismatch'):       score -= 20
    if factors.get('suspicious_redirect'):       score -= 20
    if factors.get('url_shortener'):             score -= 15
    if factors.get('no_visible_name'):           score -= 15
    if factors.get('processor_unknown'):         score -= 10
    if factors.get('link_broken'):               score -= 10
    if factors.get('abandoned_website'):         score -= 10
    return max(0, min(100, score))
