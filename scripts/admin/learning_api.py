#!/usr/bin/env python3
"""
Learning Engine API — Exposes continuous improvement system status and metrics.

Endpoints:
- GET /api/learning/status — Current system learning state
- GET /api/learning/themes — All discovered themes with confidence
- GET /api/learning/summary — High-level progress summary
"""

from flask import Blueprint, jsonify
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging

learning_bp = Blueprint('learning', __name__, url_prefix='/api/learning')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
logger = logging.getLogger('learning_api')


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


@learning_bp.route('/status', methods=['GET'])
def get_status():
    """Get current learning engine status and metrics."""
    db = get_db()
    cursor = db.cursor()

    # Overall carousel metrics
    cursor.execute("""
        SELECT
            COUNT(*) as total_carousels,
            SUM(impressions) as total_impressions,
            AVG(CASE WHEN impressions > 0
                THEN ((likes + comments + shares) * 100.0 / impressions)
                ELSE 0 END) as avg_engagement_rate
        FROM carousel_metrics
    """)
    carousel_stats = dict(cursor.fetchone())

    # Learning signals (themes discovered)
    cursor.execute("""
        SELECT
            COUNT(*) as total_themes,
            AVG(confidence_score) as avg_confidence,
            COUNT(CASE WHEN confidence_score >= 0.7 THEN 1 END) as high_confidence_themes
        FROM learning_signals
    """)
    learning_stats = dict(cursor.fetchone())

    # Recommendation status
    cursor.execute("""
        SELECT
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
        FROM recommendations
    """)
    recommendation_stats = dict(cursor.fetchone())

    db.close()

    return jsonify({
        'status': 'learning_active',
        'carousel_stats': carousel_stats,
        'learning_stats': learning_stats,
        'recommendation_stats': recommendation_stats,
        'autonomy_level': _calculate_autonomy_level(learning_stats, recommendation_stats),
        'last_updated': datetime.now().isoformat()
    })


def _calculate_autonomy_level(learning_stats, rec_stats):
    """Calculate current autonomy level (0-100%) based on learning progress."""
    # Autonomy increases as we learn more themes and generate confident recommendations
    if not learning_stats or not learning_stats['total_themes']:
        return 0

    theme_factor = min(1.0, learning_stats['total_themes'] / 10)  # Max benefit at 10 themes
    confidence_factor = learning_stats['avg_confidence'] or 0  # 0-1
    rec_factor = min(1.0, rec_stats['pending'] / 5) if rec_stats['pending'] else 0  # Pendings show we're learning

    autonomy_pct = int((theme_factor * 0.4 + confidence_factor * 0.35 + rec_factor * 0.25) * 100)
    return min(100, max(0, autonomy_pct))


@learning_bp.route('/themes', methods=['GET'])
def get_themes():
    """Get all discovered themes with confidence scores."""
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

    themes = [dict(row) for row in cursor.fetchall()]
    db.close()

    # Categorize by confidence
    high_confidence = [t for t in themes if t['confidence_score'] >= 0.7]
    medium_confidence = [t for t in themes if 0.4 <= t['confidence_score'] < 0.7]
    low_confidence = [t for t in themes if t['confidence_score'] < 0.4]

    return jsonify({
        'all_themes': themes,
        'high_confidence': high_confidence,
        'medium_confidence': medium_confidence,
        'low_confidence': low_confidence,
        'total': len(themes),
        'strong_signals': len(high_confidence)
    })


@learning_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get high-level learning progress summary."""
    db = get_db()
    cursor = db.cursor()

    # Last 7 days metrics
    cursor.execute("""
        SELECT
            COUNT(*) as carousels_last_7d,
            SUM(impressions) as impressions_last_7d,
            ROUND(AVG(CASE WHEN impressions > 0
                THEN ((likes + comments + shares) * 100.0 / impressions)
                ELSE 0 END), 2) as engagement_rate_last_7d
        FROM carousel_metrics
        WHERE posted_at > datetime('now', '-7 days')
    """)
    week_stats = dict(cursor.fetchone())

    # Last 30 days metrics
    cursor.execute("""
        SELECT
            COUNT(*) as carousels_last_30d,
            SUM(impressions) as impressions_last_30d,
            ROUND(AVG(CASE WHEN impressions > 0
                THEN ((likes + comments + shares) * 100.0 / impressions)
                ELSE 0 END), 2) as engagement_rate_last_30d
        FROM carousel_metrics
        WHERE posted_at > datetime('now', '-30 days')
    """)
    month_stats = dict(cursor.fetchone())

    # System learning progress
    cursor.execute("""
        SELECT
            COUNT(DISTINCT theme) as discovered_themes,
            COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence_themes,
            ROUND(AVG(confidence_score), 3) as avg_theme_confidence
        FROM learning_signals
    """)
    learning_progress = dict(cursor.fetchone())

    # Recommendation acceptance rate
    cursor.execute("""
        SELECT
            COUNT(*) as total_recommendations,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count
        FROM recommendations
    """)
    rec_data = dict(cursor.fetchone())

    acceptance_rate = 0
    if rec_data['total_recommendations'] > 0:
        acceptance_rate = (rec_data['approved_count'] / rec_data['total_recommendations']) * 100

    db.close()

    return jsonify({
        'learning_progress': {
            'discovered_themes': learning_progress['discovered_themes'] or 0,
            'high_confidence_themes': learning_progress['high_confidence_themes'] or 0,
            'avg_theme_confidence': learning_progress['avg_theme_confidence'] or 0.0,
        },
        'recommendation_quality': {
            'total_recommendations': rec_data['total_recommendations'] or 0,
            'approved': rec_data['approved_count'] or 0,
            'rejected': rec_data['rejected_count'] or 0,
            'acceptance_rate_pct': round(acceptance_rate, 1),
        },
        'performance_trend': {
            'last_7_days': week_stats,
            'last_30_days': month_stats,
            'trend': _calculate_trend(week_stats['engagement_rate_last_7d'], month_stats['engagement_rate_last_30d']),
        },
        'generated_at': datetime.now().isoformat(),
    })


def _calculate_trend(recent: float, overall: float) -> str:
    """Calculate trend: 'improving', 'stable', or 'declining'."""
    if not recent or not overall:
        return 'unknown'

    pct_change = ((recent - overall) / overall) * 100 if overall > 0 else 0

    if pct_change > 5:
        return 'improving'
    elif pct_change < -5:
        return 'declining'
    else:
        return 'stable'


@learning_bp.route('/health', methods=['GET'])
def health():
    """Health check for learning API."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM carousel_metrics LIMIT 1")
        db.close()
        return jsonify({'status': 'healthy'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
