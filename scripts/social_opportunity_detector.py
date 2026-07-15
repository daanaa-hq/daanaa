#!/usr/bin/env python3
"""
Social Opportunity Detector — Autonomously finds trending nonprofit/giving topics to comment on.

Monitors:
- Nonprofit sector trends (news, policy, sector insights)
- Giving trends (donor behavior, funding gaps, emerging movements)
- Financial health discussions (nonprofit budgeting, reserves, sustainability)
- Related conversations on LinkedIn/Twitter (sector thought leaders)

Detects opportunities for:
- High-quality comments that add value + drive traffic
- Weekly carousel themes based on what's trending
- Educational content that positions Daanaa as expertise

Philosophy:
- Only comment where Daanaa can genuinely add value
- Never spam or force relevance
- Witty + intelligent, not corporate
- Drive traffic through quality, not manipulation
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

logger = logging.getLogger('social_opportunity_detector')
logger.setLevel(logging.INFO)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

# Keywords that indicate good comment opportunities
NONPROFIT_KEYWORDS = [
    'nonprofit', 'ngo', 'charity', 'foundation', 'giving',
    'donor', 'fundraising', 'nonprofit finance', '501c3',
    'sector', 'civil society', 'impact', 'social good'
]

FINANCIAL_HEALTH_KEYWORDS = [
    'nonprofit budget', 'operating reserve', 'financial health',
    'nonprofit sustainability', 'cash flow', 'fundraising gap',
    'donor concentration', 'revenue diversity'
]

OPPORTUNITY_THEMES = {
    'financial_crisis': {
        'keywords': ['nonprofit crisis', 'budget cuts', 'economic downturn', 'funding crisis'],
        'angle': 'Daanaa data shows X% of orgs lack emergency reserves'
    },
    'sector_insight': {
        'keywords': ['nonprofit trends', 'sector evolution', 'giving trends', 'donor behavior'],
        'angle': 'Our analysis of 500K+ filings reveals...'
    },
    'policy_change': {
        'keywords': ['tax policy', 'charitable giving', '501c3 rules', 'nonprofit regulation'],
        'angle': 'Here\'s what this means for nonprofits based on our data'
    },
    'thought_leadership': {
        'keywords': ['nonprofit leader', 'exec director', 'nonprofit strategy', 'nonprofit growth'],
        'angle': 'Small orgs can compete — data shows...'
    },
}


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def init_opportunity_tables():
    """Create tables for opportunity tracking."""
    db = get_db()
    cursor = db.cursor()

    # Detected opportunities (from LinkedIn/trends)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_url TEXT,
            title TEXT NOT NULL,
            description TEXT,
            opportunity_type TEXT,
            keywords TEXT,
            quality_score REAL,
            relevance_angle TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comment_generated BOOLEAN DEFAULT 0,
            comment_text TEXT,
            published_at TIMESTAMP,
            engagement_count INTEGER DEFAULT 0
        )
    """)

    # Weekly themes (autonomously curated)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_starting DATE NOT NULL UNIQUE,
            theme_title TEXT NOT NULL,
            theme_angle TEXT,
            data_hook TEXT,
            confidence_score REAL,
            reason TEXT,
            founder_approved BOOLEAN DEFAULT 0,
            published_carousel_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


def detect_opportunities():
    """
    Detect trending nonprofit/giving topics.
    In production, would scan LinkedIn API, Twitter, sector news RSS.
    For now, uses engagement patterns + sector data.
    """
    logger.info("Detecting social opportunities...")
    db = get_db()
    cursor = db.cursor()

    # Analyze recent carousel engagement to find trending themes
    cursor.execute("""
        SELECT
            engagement_themes,
            COUNT(*) as count,
            AVG(CASE WHEN impressions > 0
                THEN ((likes + comments + shares) * 100.0 / impressions)
                ELSE 0 END) as avg_engagement
        FROM carousel_metrics
        WHERE posted_at > datetime('now', '-14 days')
        GROUP BY engagement_themes
        ORDER BY avg_engagement DESC
        LIMIT 10
    """)

    trending_themes = cursor.fetchall()

    opportunities = []

    for theme_data in trending_themes:
        themes = json.loads(theme_data['engagement_themes'] or '{}')

        for theme_name in themes:
            # Check if we already have an opportunity for this theme
            cursor.execute("""
                SELECT id FROM social_opportunities
                WHERE opportunity_type = ?
                AND detected_at > datetime('now', '-7 days')
            """, (theme_name,))

            if cursor.fetchone():
                continue  # Already detected

            # Create opportunity record
            opportunity = {
                'source': 'internal_trending',
                'title': f"Trending in nonprofit data: {theme_name.replace('_', ' ')}",
                'opportunity_type': theme_name,
                'quality_score': min(0.95, theme_data['avg_engagement'] / 5.0),  # Normalize to 0-1
                'relevance_angle': _generate_angle(theme_name),
            }

            cursor.execute("""
                INSERT INTO social_opportunities
                (source, title, opportunity_type, quality_score, relevance_angle)
                VALUES (?, ?, ?, ?, ?)
            """, (
                opportunity['source'],
                opportunity['title'],
                opportunity['opportunity_type'],
                opportunity['quality_score'],
                opportunity['relevance_angle'],
            ))

            opportunities.append(opportunity)

    db.commit()
    logger.info(f"Detected {len(opportunities)} trending opportunities")
    db.close()

    return opportunities


def _generate_angle(theme_name: str) -> str:
    """Generate a comment angle for a trending theme."""
    angles = {
        'financial_health': "We analyzed 465K+ nonprofit 990s. Here's what financial health actually looks like.",
        'nonprofit_inequality': "500K nonprofits, huge inequality: data shows why small orgs struggle.",
        'funding_gaps': "The $100B funding gap is real. Data from 465K+ orgs shows where.",
        'hidden_gems': "Best-kept secret: 34K high-performing nonprofits nobody knows about.",
        'sector_trends': "After analyzing 500K+ filings, we discovered 3 shifts reshaping the sector.",
        'transparency': "Transparency matters. Here's what 990 data reveals about accountability.",
    }

    return angles.get(theme_name, f"We analyzed 500K+ nonprofit filings. Here's what we found about {theme_name}.")


def curate_weekly_theme():
    """
    Autonomously curate next week's carousel theme.
    Uses: trending opportunities + learning signals + sector calendar.
    """
    logger.info("Curating weekly theme...")
    db = get_db()
    cursor = db.cursor()

    # Get trending opportunities (high quality)
    cursor.execute("""
        SELECT opportunity_type, relevance_angle, quality_score
        FROM social_opportunities
        WHERE quality_score >= 0.7
        AND published_at IS NULL
        ORDER BY quality_score DESC
        LIMIT 5
    """)

    opportunities = cursor.fetchall()

    # Get learning signals (what themes perform well)
    cursor.execute("""
        SELECT theme, avg_engagement_rate, confidence_score
        FROM learning_signals
        WHERE confidence_score >= 0.7
        ORDER BY avg_engagement_rate DESC
        LIMIT 3
    """)

    learning_signals = cursor.fetchall()

    # Pick the best theme
    best_theme = None
    best_score = 0

    for opp in opportunities:
        # Combine opportunity quality + learning confidence
        combined_score = opp['quality_score'] * 0.6 + 0.4

        if combined_score > best_score:
            best_score = combined_score
            best_theme = opp

    if not best_theme and learning_signals:
        # Fallback to high-performing learning signal
        best_theme = learning_signals[0]

    if best_theme:
        week_starting = (datetime.now() + timedelta(days=(7 - datetime.now().weekday()))).date()

        theme_title = f"The {best_theme['opportunity_type'].replace('_', ' ').title()} Story"
        data_hook = _generate_data_hook(best_theme['opportunity_type'])

        cursor.execute("""
            INSERT INTO weekly_themes
            (week_starting, theme_title, theme_angle, data_hook, confidence_score, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_starting) DO UPDATE SET
                theme_title = excluded.theme_title,
                confidence_score = excluded.confidence_score
        """, (
            week_starting,
            theme_title,
            best_theme['relevance_angle'],
            data_hook,
            best_score,
            'Auto-curated from trending opportunities + learning signals'
        ))

        logger.info(f"Curated theme: {theme_title} ({best_score:.0%} confidence)")

    db.commit()
    db.close()


def _generate_data_hook(theme: str) -> str:
    """Generate a data-driven hook for the theme."""
    hooks = {
        'financial_health': "We read 465,306 990s. Here's the reserve reality.",
        'nonprofit_inequality': "500K nonprofits. Massive funding gap. We have the data.",
        'sector_trends': "Five years of 990 data reveal three shifts reshaping giving.",
        'hidden_gems': "34K high-performing nonprofits nobody's heard of. We found them.",
    }

    return hooks.get(theme, f"Data-driven insights into {theme}")


def get_pending_opportunities():
    """Get opportunities ready for commenting."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, title, source_url, relevance_angle, quality_score, opportunity_type
        FROM social_opportunities
        WHERE comment_generated = 0
        AND quality_score >= 0.75
        AND detected_at > datetime('now', '-7 days')
        ORDER BY quality_score DESC
        LIMIT 10
    """)

    opportunities = [dict(row) for row in cursor.fetchall()]
    db.close()

    return opportunities


def get_pending_weekly_themes():
    """Get weekly themes pending founder approval."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, week_starting, theme_title, theme_angle, data_hook, confidence_score
        FROM weekly_themes
        WHERE founder_approved = 0
        AND week_starting >= DATE('now')
        ORDER BY week_starting ASC
    """)

    themes = [dict(row) for row in cursor.fetchall()]
    db.close()

    return themes


def approve_weekly_theme(theme_id: int):
    """Founder approves a weekly theme."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE weekly_themes SET founder_approved = 1 WHERE id = ?
    """, (theme_id,))

    db.commit()
    db.close()

    logger.info(f"Theme {theme_id} approved by founder")


def reject_weekly_theme(theme_id: int):
    """Founder rejects a weekly theme."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM weekly_themes WHERE id = ?
    """, (theme_id,))

    db.commit()
    db.close()

    logger.info(f"Theme {theme_id} rejected by founder")


# Initialize tables on import
init_opportunity_tables()
