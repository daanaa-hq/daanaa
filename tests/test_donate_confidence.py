"""Tests for the extracted donate_confidence module (Task 1).

These are the exact same test cases that would validate
donation_link_pipeline.py's original score_confidence()/identity_match() —
extraction must not change behavior, only location.
"""
from scripts.donate_confidence import score_confidence, identity_match


def test_score_confidence_all_positive_factors():
    factors = {
        'found_on_official_website': True,
        'nonprofit_name_visible': True,
        'website_confidence_90': True,
        'processor_recognized': True,
        'no_suspicious_redirects': True,
        'city_state_match': True,
        'branding_matches': True,
        'link_works': True,
        'ein_visible': True,
    }
    # 30+20+15+10+10+5+5+5+5 = 105, clamped to 100
    assert score_confidence(factors) == 100


def test_score_confidence_empty_factors_is_zero():
    assert score_confidence({}) == 0


def test_score_confidence_deductions_clamp_at_zero():
    factors = {
        'name_mismatch': True,
        'website_not_official': True,
        'not_from_official_site': True,
    }
    # -40 + -30 + -25 = -95, clamped to 0
    assert score_confidence(factors) == 0


def test_score_confidence_known_partial_case():
    factors = {
        'found_on_official_website': True,  # +30
        'processor_recognized': True,        # +10
        'link_broken': True,                 # -10
    }
    assert score_confidence(factors) == 30


def test_identity_match_exact():
    level, ratio = identity_match(
        "Tech For Good Foundation",
        "Welcome to Tech For Good Foundation, providing technology training."
    )
    assert level == 'exact'
    assert ratio == 1.0


def test_identity_match_mismatch():
    level, ratio = identity_match(
        "Tech For Good Foundation",
        "This page is about completely unrelated topics with no overlap words."
    )
    assert level == 'mismatch'
    assert ratio == 0.0


def test_identity_match_stop_words_ignored():
    # "the", "of", "and", "foundation" are stop words — only "tech", "good" count
    level, ratio = identity_match(
        "The Tech and Good Foundation",
        "tech good"
    )
    assert level == 'exact'
    assert ratio == 1.0
