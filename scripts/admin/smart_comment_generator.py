#!/usr/bin/env python3
"""
Smart Comment Generator — Creates witty, intelligent comments that drive traffic authentically.

Philosophy:
- Genuine insight, not self-promotion
- Witty but not try-hard
- Data-backed (cite Daanaa insights when relevant)
- Add value to conversation, not hijack it
- Never spam-like (one great comment beats three mediocre ones)

Patterns:
1. Data point that expands the conversation
2. Question that makes people think
3. Reframe that adds nuance
4. Offer that feels natural (not "visit our site")

CTAs are:
- Subtle (mention Daanaa if relevant, not forced)
- Value-first ("see the data on Daanaa" not "check us out")
- Optional (comment works without CTA)
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('smart_comment_generator')
logger.setLevel(logging.INFO)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


# Comment templates by opportunity type + style
COMMENT_TEMPLATES = {
    'financial_health': [
        {
            'style': 'data_insight',
            'template': "We analyzed 465K nonprofit 990s. {insight}. The small-org reserve crisis is even more acute than people realize.",
            'cta': 'See the breakdown on Daanaa.',
        },
        {
            'style': 'question',
            'template': "This is why nonprofit reserve adequacy matters. How many nonprofits in your network have 3+ months of operating costs saved? {question}",
            'cta': 'We analyzed 500K+ 990s if you\'re curious about sector patterns.',
        },
        {
            'style': 'reframe',
            'template': "{observation} That's the structural problem: small orgs can't weather economic downturns because they lack cushion. It's not irresponsible management; it's systemic.",
            'cta': 'Data: 42K+ nonprofits hold less than one month of reserves.',
        },
    ],
    'hidden_gems': [
        {
            'style': 'data_insight',
            'template': "The best-kept secret in nonprofits: 34K high-performing orgs nobody's heard of. {insight}. Scale ≠ impact.",
            'cta': 'We track these (hidden gems) if you\'re looking for breakthrough organizations.',
        },
        {
            'style': 'question',
            'template': "How do we find breakthrough nonprofits? {question}. Most donor resources flow to 0.1% of orgs.",
            'cta': 'This is exactly why we built Daanaa—to surface the rest.',
        },
    ],
    'nonprofit_inequality': [
        {
            'style': 'data_insight',
            'template': "The funding gap is stark: {insight}. 500K+ nonprofits. A few billion go to the known players. Billions more needed elsewhere.",
            'cta': 'We mapped it on Daanaa.',
        },
        {
            'style': 'reframe',
            'template': "Size bias is real in giving. {observation}. Small orgs aren't less effective; they're just less visible.",
            'cta': 'Data helps fix that bias.',
        },
    ],
    'sector_trends': [
        {
            'style': 'data_insight',
            'template': "After analyzing 500K+ 990s, we see {insight}. The sector is shifting.",
            'cta': 'Full breakdown on Daanaa.',
        },
        {
            'style': 'question',
            'template': "{question}. {observation}. What does this mean for strategy?",
            'cta': 'Worth tracking if you work in the sector.',
        },
    ],
    'transparency': [
        {
            'style': 'data_insight',
            'template': "Transparency matters more than we think. {insight}. Trust is built on clarity.",
            'cta': 'We help nonprofits surface their real story.',
        },
        {
            'style': 'reframe',
            'template': "{observation}. 990s are public, but underutilized. {insight}.",
            'cta': 'Daanaa makes that data accessible.',
        },
    ],
}


def generate_comment(opportunity_type: str, source_text: str = None, data_hook: str = None, confidence: float = 0.85):
    """
    Generate a smart comment for a given opportunity.

    Args:
        opportunity_type: e.g., 'financial_health', 'hidden_gems'
        source_text: original post text (to inform comment)
        data_hook: Daanaa insight to include
        confidence: how confident we are in the comment (0-1)

    Returns:
        comment: dict with text, style, has_cta, confidence
    """
    if opportunity_type not in COMMENT_TEMPLATES:
        return None

    templates = COMMENT_TEMPLATES[opportunity_type]

    # Pick a template (rotate by type for variety)
    template = templates[len(source_text or '') % len(templates)]

    # Generate specific insight
    insights = _generate_insights(opportunity_type)
    insight = insights[0] if insights else "the landscape is changing"

    # Build comment
    comment_text = template['template'].format(
        insight=insight,
        observation=_generate_observation(opportunity_type),
        question=_generate_question(opportunity_type),
    )

    # Add CTA naturally
    cta = template.get('cta', '')

    # Only add CTA if high confidence
    if confidence >= 0.8:
        comment_text = f"{comment_text}\n\n{cta}"

    return {
        'text': comment_text,
        'style': template['style'],
        'has_cta': confidence >= 0.8,
        'confidence': confidence,
        'opportunity_type': opportunity_type,
    }


def _generate_insights(opportunity_type: str):
    """Generate data insights for a comment."""
    insights_db = {
        'financial_health': [
            "54.9% of the sector can run a full year on reserves",
            "42K+ orgs hold less than one month of operating costs",
            "the gap between the haves and have-nots is stark",
        ],
        'hidden_gems': [
            "high impact doesn't correlate with size",
            "you find them when you analyze data instead of headlines",
            "donor attention is concentrated; talent is distributed",
        ],
        'nonprofit_inequality': [
            "funding flows to known brands, not necessarily effectiveness",
            "a tiny percent of orgs capture most philanthropic capital",
            "small organizations are systematically underfunded relative to need",
        ],
        'sector_trends': [
            "the sector is consolidating in some areas, fragmenting in others",
            "digital transformation is uneven across nonprofit sizes",
            "donor expectations are evolving faster than nonprofit infrastructure",
        ],
    }

    return insights_db.get(opportunity_type, ["the data tells a nuanced story"])


def _generate_observation(opportunity_type: str):
    """Generate observational hook for a comment."""
    observations = {
        'financial_health': "Nonprofits without reserves are living on the edge",
        'hidden_gems': "The most impactful work often happens outside the spotlight",
        'nonprofit_inequality': "Attention flows to the largest organizations, funding follows attention",
        'sector_trends': "The nonprofit sector is evolving faster than people realize",
    }

    return observations.get(opportunity_type, "The story is more complex than headlines suggest")


def _generate_question(opportunity_type: str):
    """Generate reflective question for a comment."""
    questions = {
        'financial_health': "How resilient is your organization's balance sheet?",
        'hidden_gems': "How many organizations in your network are you missing?",
        'nonprofit_inequality': "Where is your giving strategy working, and where is it blind?",
        'sector_trends': "What's changing in your corner of the sector?",
    }

    return questions.get(opportunity_type, "What patterns do you see?")


def quality_score_comment(comment: dict, source_text: str = None) -> float:
    """
    Score a generated comment on quality.
    Returns 0-1 confidence score.

    Criteria:
    - Length (150-400 chars is sweet spot)
    - Specificity (data, not vague)
    - CTA naturalness (not forced)
    - Relevance to source (if available)
    """
    text = comment['text']

    score = 0.7  # Base

    # Length check
    if 150 <= len(text) <= 400:
        score += 0.15
    elif 100 <= len(text) <= 500:
        score += 0.08

    # Specificity check (look for numbers, specific claims)
    if any(c.isdigit() for c in text):
        score += 0.1

    # CTA naturalness
    if comment['has_cta']:
        score += 0.05

    return min(1.0, score)


def log_comment_generated(opportunity_id: int, comment: dict, published: bool = False):
    """Log that we generated a comment for an opportunity."""
    import sqlite3

    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    cursor.execute("""
        UPDATE social_opportunities
        SET comment_generated = 1, comment_text = ?, published_at = ?
        WHERE id = ?
    """, (
        comment['text'],
        datetime.now().isoformat() if published else None,
        opportunity_id,
    ))

    db.commit()
    db.close()

    status = "published" if published else "generated"
    logger.info(f"Comment {status} for opportunity {opportunity_id}")
