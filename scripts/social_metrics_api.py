#!/usr/bin/env python3
"""
Social Media Metrics API — Aggregates engagement data for learning engine.

Endpoints:
- GET /api/social/metrics — Aggregate engagement (impressions, clicks, engagement rate)
- GET /api/social/carousel/{carousel_id} — Performance of a single carousel
- GET /api/social/themes — Extract engagement themes from comments
- POST /api/social/log — Record new engagement event from LinkedIn webhook
- GET /api/social/recommendations — AI-suggested next carousel topics (learning engine output)
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

social_metrics_bp = Blueprint('social_metrics', __name__, url_prefix='/api/social')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
logger = logging.getLogger('social_metrics')


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


def init_social_tables():
    """Create tables for social media metrics tracking."""
    db = get_db()
    cursor = db.cursor()

    # Carousel performance log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carousel_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carousel_id TEXT NOT NULL UNIQUE,
            carousel_type TEXT,
            title TEXT,
            posted_at TIMESTAMP,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            comments_text TEXT,
            engagement_themes TEXT,
            sentiment_avg REAL,
            last_synced TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Engagement events (for real-time tracking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engagement_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carousel_id TEXT NOT NULL,
            event_type TEXT,
            count INTEGER,
            details TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (carousel_id) REFERENCES carousel_metrics(carousel_id)
        )
    """)

    # Learning signals (what we learn from engagement)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme TEXT NOT NULL,
            carousel_count INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0,
            last_seen TIMESTAMP,
            confidence_score REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Recommendations (AI-suggested next topics)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            confidence_score REAL,
            estimated_engagement REAL,
            related_themes TEXT,
            status TEXT DEFAULT 'pending',
            founder_approved BOOLEAN DEFAULT 0,
            posted_carousel_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


@social_metrics_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get aggregate social media metrics (all carousels, last 90 days)."""
    db = get_db()
    cursor = db.cursor()

    # Get metrics from last 90 days
    cursor.execute("""
        SELECT
            COUNT(*) as carousel_count,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(likes) as total_likes,
            SUM(comments) as total_comments,
            SUM(shares) as total_shares,
            ROUND(AVG(CASE WHEN impressions > 0
                THEN ((likes + comments + shares) * 100.0 / impressions)
                ELSE 0 END), 2) as avg_engagement_rate
        FROM carousel_metrics
        WHERE posted_at > datetime('now', '-90 days')
    """)

    row = cursor.fetchone()
    db.close()

    metrics = {
        'carousel_count': row['carousel_count'] or 0,
        'total_impressions': row['total_impressions'] or 0,
        'total_clicks': row['total_clicks'] or 0,
        'total_likes': row['total_likes'] or 0,
        'total_comments': row['total_comments'] or 0,
        'total_shares': row['total_shares'] or 0,
        'avg_engagement_rate': row['avg_engagement_rate'] or 0.0,
        'last_30_days': get_metrics_timeframe(30),
        'last_7_days': get_metrics_timeframe(7),
        'trending_themes': get_trending_themes(),
    }

    return jsonify(metrics)


def get_metrics_timeframe(days: int):
    """Helper: Get metrics for a specific timeframe."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute(f"""
        SELECT
            COUNT(*) as carousel_count,
            SUM(impressions) as total_impressions,
            ROUND(AVG(CASE WHEN impressions > 0
                THEN ((likes + comments + shares) * 100.0 / impressions)
                ELSE 0 END), 2) as avg_engagement_rate
        FROM carousel_metrics
        WHERE posted_at > datetime('now', '-{days} days')
    """)

    row = cursor.fetchone()
    db.close()

    return {
        'period_days': days,
        'carousel_count': row['carousel_count'] or 0,
        'total_impressions': row['total_impressions'] or 0,
        'avg_engagement_rate': row['avg_engagement_rate'] or 0.0
    }


@social_metrics_bp.route('/carousel/<carousel_id>', methods=['GET'])
def get_carousel_metrics(carousel_id):
    """Get performance metrics for a single carousel."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM carousel_metrics
        WHERE carousel_id = ?
    """, (carousel_id,))

    row = cursor.fetchone()
    db.close()

    if not row:
        return jsonify({'error': 'Carousel not found'}), 404

    carousel = dict(row)
    carousel['engagement_themes'] = json.loads(carousel['engagement_themes'] or '{}')
    carousel['comments'] = carousel['comments'] or []

    return jsonify(carousel)


def get_trending_themes():
    """Extract trending themes from engagement data."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            theme,
            carousel_count,
            avg_engagement_rate,
            confidence_score
        FROM learning_signals
        WHERE last_seen > datetime('now', '-30 days')
        ORDER BY avg_engagement_rate DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()
    db.close()

    return [dict(row) for row in rows]


@social_metrics_bp.route('/themes', methods=['GET'])
def get_themes():
    """Get engagement themes extracted from comments."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            theme,
            carousel_count,
            avg_engagement_rate,
            confidence_score,
            last_seen
        FROM learning_signals
        ORDER BY confidence_score DESC, last_seen DESC
    """)

    rows = cursor.fetchall()
    db.close()

    themes = [dict(row) for row in rows]
    return jsonify({
        'themes': themes,
        'total_themes': len(themes),
        'high_confidence': sum(1 for t in themes if t['confidence_score'] >= 0.7),
        'last_updated': datetime.now().isoformat()
    })


@social_metrics_bp.route('/log', methods=['POST'])
def log_engagement():
    """Record a new engagement event (from LinkedIn webhook or manual entry)."""
    data = request.get_json()

    carousel_id = data.get('carousel_id')
    event_type = data.get('event_type')  # 'impression', 'click', 'like', 'comment', 'share'
    count = data.get('count', 1)
    details = data.get('details', {})

    if not carousel_id or not event_type:
        return jsonify({'error': 'carousel_id and event_type required'}), 400

    db = get_db()
    cursor = db.cursor()

    # Insert engagement event
    cursor.execute("""
        INSERT INTO engagement_events (carousel_id, event_type, count, details)
        VALUES (?, ?, ?, ?)
    """, (carousel_id, event_type, count, json.dumps(details)))

    # Update carousel_metrics aggregates
    cursor.execute(f"""
        UPDATE carousel_metrics
        SET {event_type}s = {event_type}s + ?
        WHERE carousel_id = ?
    """, (count, carousel_id))

    db.commit()
    db.close()

    return jsonify({'status': 'logged', 'carousel_id': carousel_id}), 201


@social_metrics_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get AI-recommended next carousel topics (from learning engine)."""
    db = get_db()
    cursor = db.cursor()

    # Get top recommendations
    cursor.execute("""
        SELECT
            id,
            topic,
            confidence_score,
            estimated_engagement,
            related_themes,
            status
        FROM recommendations
        WHERE status = 'pending'
        ORDER BY confidence_score DESC, estimated_engagement DESC
        LIMIT 10
    """)

    recommendations = [dict(row) for row in cursor.fetchall()]
    db.close()

    for rec in recommendations:
        rec['related_themes'] = json.loads(rec['related_themes'] or '[]')

    return jsonify({
        'recommendations': recommendations,
        'total_pending': len(recommendations),
        'high_confidence': sum(1 for r in recommendations if r['confidence_score'] >= 0.8),
        'generated_at': datetime.now().isoformat()
    })


@social_metrics_bp.route('/recommendations/<int:rec_id>/approve', methods=['POST'])
def approve_recommendation(rec_id):
    """Approve a recommendation for carousel creation."""
    data = request.get_json()
    carousel_id = data.get('carousel_id')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE recommendations
        SET status = 'approved', founder_approved = 1, posted_carousel_id = ?
        WHERE id = ?
    """, (carousel_id, rec_id))

    db.commit()
    db.close()

    return jsonify({'status': 'approved', 'recommendation_id': rec_id})


@social_metrics_bp.route('/recommendations/<int:rec_id>/reject', methods=['POST'])
def reject_recommendation(rec_id):
    """Reject a recommendation."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE recommendations
        SET status = 'rejected'
        WHERE id = ?
    """, (rec_id,))

    db.commit()
    db.close()

    return jsonify({'status': 'rejected', 'recommendation_id': rec_id})


@social_metrics_bp.route('/health', methods=['GET'])
def health():
    """Health check for metrics API."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM carousel_metrics LIMIT 1")
        db.close()
        return jsonify({'status': 'healthy'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


# Initialize tables on module load
init_social_tables()
