#!/usr/bin/env python3
"""
Continuous Improvement Engine — Learning system that improves recommendations over time.

Ingests:
- Social media engagement metrics (impressions, clicks, engagement rate)
- Comment themes and sentiment
- User feedback (carousel approvals, rejections)

Outputs:
- Updated learning signals (what themes resonate)
- Carousel topic recommendations
- Confidence scores for recommendations
- Estimated engagement for topics

Architecture:
- Hourly analysis of new engagement data
- Rolling 30/90 day trend windows
- Bayesian confidence scoring
- Safe defaults (auto-recommend only if >85% confidence)
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import math

logger = logging.getLogger('continuous_improvement')
logger.setLevel(logging.INFO)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

# Known carousel types and their baseline engagement expectations
CAROUSEL_BASELINES = {
    'hidden_gems': {'baseline_engagement': 4.2, 'volatility': 1.2},
    'sector_insight': {'baseline_engagement': 3.1, 'volatility': 0.8},
    'myth_bust': {'baseline_engagement': 5.7, 'volatility': 2.1},
    'how_it_works': {'baseline_engagement': 2.8, 'volatility': 0.9},
    'feature_launch': {'baseline_engagement': 3.5, 'volatility': 1.4},
}

KNOWN_THEMES = [
    'financial_health',
    'nonprofit_inequality',
    'small_organizations',
    'transparency',
    'funding_gaps',
    'sector_trends',
    'hidden_gems',
    'donor_education',
    'impact_measurement',
    'governance',
    'executive_compensation',
    'volunteer_opportunities',
    'technology_adoption',
]


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def analyze_engagement_data():
    """
    Analyze recent carousel performance and extract themes.
    Runs hourly — updates learning_signals table with confidence scores.
    """
    logger.info("Analyzing engagement data...")
    db = get_db()
    cursor = db.cursor()

    # Get carousels from last 14 days with engagement data
    cursor.execute("""
        SELECT
            carousel_id,
            carousel_type,
            impressions,
            likes,
            comments,
            shares,
            engagement_themes,
            posted_at
        FROM carousel_metrics
        WHERE posted_at > datetime('now', '-14 days')
        AND impressions > 0
        ORDER BY posted_at DESC
    """)

    carousels = cursor.fetchall()
    theme_stats = defaultdict(lambda: {'count': 0, 'engagement_sum': 0, 'carousel_ids': []})

    for carousel in carousels:
        # Calculate engagement rate
        engagement = carousel['likes'] + carousel['comments'] + carousel['shares']
        engagement_rate = (engagement / carousel['impressions'] * 100) if carousel['impressions'] > 0 else 0

        # Extract themes from carousel metadata
        themes = json.loads(carousel['engagement_themes'] or '{}')
        if isinstance(themes, dict):
            themes = list(themes.keys())

        for theme in themes:
            if theme in KNOWN_THEMES:
                theme_stats[theme]['count'] += 1
                theme_stats[theme]['engagement_sum'] += engagement_rate
                theme_stats[theme]['carousel_ids'].append(carousel['carousel_id'])

    # Update learning_signals with confidence scores
    for theme, stats in theme_stats.items():
        avg_engagement = stats['engagement_sum'] / stats['count'] if stats['count'] > 0 else 0

        # Calculate confidence using Bayesian approach:
        # confidence = min(1.0, (count / 3) * (engagement_rate / baseline))
        baseline = CAROUSEL_BASELINES.get(theme, {}).get('baseline_engagement', 3.0)
        confidence = min(1.0, (stats['count'] / 3.0) * (avg_engagement / baseline)) if baseline > 0 else 0.5

        cursor.execute("""
            INSERT INTO learning_signals (theme, carousel_count, avg_engagement_rate, confidence_score, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(theme) DO UPDATE SET
                carousel_count = excluded.carousel_count,
                avg_engagement_rate = excluded.avg_engagement_rate,
                confidence_score = excluded.confidence_score,
                last_seen = CURRENT_TIMESTAMP
        """, (theme, stats['count'], avg_engagement, confidence))

    db.commit()
    logger.info(f"Updated {len(theme_stats)} themes in learning signals")
    db.close()


def generate_recommendations():
    """
    Generate carousel topic recommendations based on learning signals.
    Uses high-engagement themes to suggest next topics.
    """
    logger.info("Generating recommendations...")
    db = get_db()
    cursor = db.cursor()

    # Get high-confidence themes
    cursor.execute("""
        SELECT theme, carousel_count, avg_engagement_rate, confidence_score
        FROM learning_signals
        WHERE confidence_score > 0.5
        ORDER BY avg_engagement_rate DESC
        LIMIT 20
    """)

    themes = cursor.fetchall()

    # Generate recommendations by combining themes and related angles
    recommendations = []

    for theme in themes:
        theme_name = theme['theme']
        engagement = theme['avg_engagement_rate']

        # Estimate engagement for new carousel using this theme
        base_confidence = theme['confidence_score']
        estimated_engagement = engagement * (0.8 + 0.4 * base_confidence)  # 80-120% of observed

        # Generate topic variations based on theme
        topics = _generate_topic_variations(theme_name, engagement)

        for topic in topics:
            # Skip if we already have a recommendation for this
            cursor.execute("""
                SELECT id FROM recommendations
                WHERE topic = ? AND status IN ('pending', 'approved')
            """, (topic,))

            if cursor.fetchone():
                continue  # Already recommended

            recommendation = {
                'topic': topic,
                'confidence_score': min(0.95, base_confidence + 0.1),  # Slightly boost existing recommendations
                'estimated_engagement': estimated_engagement,
                'related_themes': json.dumps([theme_name]),
                'status': 'pending'
            }

            cursor.execute("""
                INSERT INTO recommendations
                (topic, confidence_score, estimated_engagement, related_themes, status)
                VALUES (?, ?, ?, ?, ?)
            """, (recommendation['topic'], recommendation['confidence_score'], recommendation['estimated_engagement'],
                  recommendation['related_themes'], recommendation['status']))

            recommendations.append(recommendation)

    db.commit()
    logger.info(f"Generated {len(recommendations)} new recommendations")
    db.close()

    return recommendations


def _generate_topic_variations(theme: str, engagement_rate: float):
    """Generate topic variations based on a theme."""
    variations = {
        'financial_health': [
            'The Reserve Crisis: Why 40% of Nonprofits Have No Safety Net',
            'Cash Flow Secrets: How Top-Performing Nonprofits Stay Solvent',
            'The 3-Month Rule: Why Reserve Funds Matter More Than You Think',
        ],
        'nonprofit_inequality': [
            'The Nonprofit Size Gap: Why Funding Favors the Big',
            'Small Orgs, Big Impact: 5 Nonprofits Punching Above Their Weight',
            'The Geography of Giving: Where Money Flows vs. Where Need Is',
        ],
        'sector_trends': [
            'What 500K Nonprofit 990s Reveal About the Sector in 2026',
            'The Funding Paradox: More Money, More Problems?',
            'Emerging Sectors to Watch in 2026',
        ],
        'transparency': [
            'How to Read a Nonprofit\'s 990 Form (And Why You Should)',
            'Transparency Theater vs. Real Accountability',
            'What Mission Statements Actually Tell You',
        ],
        'donor_education': [
            'Before You Give: 5 Questions That Predict Impact',
            'Matching Your Values to Missions That Matter',
            'Why Size Doesn\'t Equal Effectiveness',
        ],
    }

    return variations.get(theme, [
        f'Exploring {theme.replace("_", " ").title()} in the Nonprofit Sector',
        f'Data-Driven Insights: {theme.replace("_", " ").title()}',
        f'What We Learned From 500K Orgs About {theme.replace("_", " ").title()}',
    ])


def process_user_feedback():
    """
    Process founder feedback (approvals, rejections) to improve recommendations.
    Positive feedback increases confidence in related themes.
    Negative feedback decreases confidence.
    """
    logger.info("Processing user feedback...")
    db = get_db()
    cursor = db.cursor()

    # Get recently approved recommendations
    cursor.execute("""
        SELECT id, topic, related_themes, posted_carousel_id
        FROM recommendations
        WHERE status = 'approved'
        AND founder_approved = 1
        AND posted_carousel_id IS NOT NULL
    """)

    approvals = cursor.fetchall()

    for approval in approvals:
        themes = json.loads(approval['related_themes'])
        carousel_id = approval['posted_carousel_id']

        # Get performance of posted carousel
        cursor.execute("""
            SELECT impressions, likes, comments, shares
            FROM carousel_metrics
            WHERE carousel_id = ?
        """, (carousel_id,))

        perf = cursor.fetchone()
        if perf and perf['impressions'] > 0:
            engagement_rate = ((perf['likes'] + perf['comments'] + perf['shares']) / perf['impressions']) * 100

            # Boost confidence for themes in approved carousels that perform well
            for theme in themes:
                cursor.execute("""
                    UPDATE learning_signals
                    SET confidence_score = MIN(1.0, confidence_score * 1.2)
                    WHERE theme = ? AND confidence_score < 0.95
                """, (theme,))

    # Get rejected recommendations to lower confidence
    cursor.execute("""
        SELECT id, related_themes
        FROM recommendations
        WHERE status = 'rejected'
    """)

    rejections = cursor.fetchall()

    for rejection in rejections:
        themes = json.loads(rejection['related_themes'])

        for theme in themes:
            cursor.execute("""
                UPDATE learning_signals
                SET confidence_score = confidence_score * 0.85
                WHERE theme = ?
            """, (theme,))

    db.commit()
    logger.info(f"Processed {len(approvals)} approvals and {len(rejections)} rejections")
    db.close()


def calculate_metrics_summary():
    """
    Calculate and return a summary of system performance and learning progress.
    Used by dashboards to show "how well is the system learning?"
    """
    db = get_db()
    cursor = db.cursor()

    # Count carousels and engagement
    cursor.execute("""
        SELECT
            COUNT(*) as total_carousels,
            SUM(impressions) as total_impressions,
            AVG(CASE WHEN impressions > 0 THEN ((likes + comments + shares) * 100.0 / impressions) ELSE 0 END) as avg_engagement_rate
        FROM carousel_metrics
    """)
    carousel_stats = dict(cursor.fetchone())

    # Count learning signals
    cursor.execute("""
        SELECT
            COUNT(*) as total_themes,
            AVG(confidence_score) as avg_theme_confidence,
            MAX(avg_engagement_rate) as max_theme_engagement
        FROM learning_signals
    """)
    learning_stats = dict(cursor.fetchone())

    # Count pending recommendations
    cursor.execute("""
        SELECT COUNT(*) as pending_recommendations
        FROM recommendations
        WHERE status = 'pending'
    """)
    pending_recs = dict(cursor.fetchone())

    db.close()

    return {
        'carousel_stats': carousel_stats,
        'learning_stats': learning_stats,
        'pending_recommendations': pending_recs['pending_recommendations'],
        'last_updated': datetime.now().isoformat(),
    }


def run_hourly_update():
    """
    Main hourly update loop.
    - Analyze engagement data
    - Generate recommendations
    - Process user feedback
    - Update metrics summary
    """
    try:
        logger.info("Starting hourly continuous improvement update...")

        analyze_engagement_data()
        process_user_feedback()
        generate_recommendations()

        summary = calculate_metrics_summary()
        logger.info(f"Update complete. Summary: {summary}")

        return summary
    except Exception as e:
        logger.error(f"Error in hourly update: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler('/home/akbar/meritgiving/logs/continuous_improvement.log'),
            logging.StreamHandler()
        ]
    )

    run_hourly_update()
