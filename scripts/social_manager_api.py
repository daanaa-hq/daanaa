#!/usr/bin/env python3
"""
Social Manager API — Dashboard for reviewing autonomously curated content.

Endpoints:
- GET /api/social-manager/weekly-themes — Pending weekly themes
- POST /api/social-manager/weekly-themes/{id}/approve — Approve theme
- POST /api/social-manager/weekly-themes/{id}/reject — Reject theme
- GET /api/social-manager/opportunities — Trending comment opportunities
- GET /api/social-manager/comments — Generated comments awaiting review
- POST /api/social-manager/comments/{id}/publish — Publish comment
"""

from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging

social_manager_bp = Blueprint('social_manager', __name__, url_prefix='/api/social-manager')

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
logger = logging.getLogger('social_manager_api')


def get_db():
    db = sqlite3.connect(str(DB))
    db.row_factory = sqlite3.Row
    return db


@social_manager_bp.route('/weekly-themes', methods=['GET'])
def get_weekly_themes():
    """Get pending weekly themes for founder review."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, week_starting, theme_title, theme_angle, data_hook, confidence_score
        FROM weekly_themes
        WHERE founder_approved = 0
        AND week_starting >= DATE('now')
        ORDER BY confidence_score DESC
    """)

    themes = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({
        'pending_themes': themes,
        'total': len(themes),
        'high_confidence': sum(1 for t in themes if t['confidence_score'] >= 0.85),
    })


@social_manager_bp.route('/weekly-themes/<int:theme_id>/approve', methods=['POST'])
def approve_theme(theme_id: int):
    """Approve a weekly theme for carousel creation."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE weekly_themes SET founder_approved = 1 WHERE id = ?
    """, (theme_id,))

    db.commit()
    db.close()

    logger.info(f"Theme {theme_id} approved")

    return jsonify({'status': 'approved', 'theme_id': theme_id})


@social_manager_bp.route('/weekly-themes/<int:theme_id>/reject', methods=['POST'])
def reject_theme(theme_id: int):
    """Reject a weekly theme."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM weekly_themes WHERE id = ?
    """, (theme_id,))

    db.commit()
    db.close()

    logger.info(f"Theme {theme_id} rejected")

    return jsonify({'status': 'rejected', 'theme_id': theme_id})


@social_manager_bp.route('/opportunities', methods=['GET'])
def get_opportunities():
    """Get trending opportunities for commenting."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, title, opportunity_type, quality_score, relevance_angle
        FROM social_opportunities
        WHERE comment_generated = 0
        AND quality_score >= 0.75
        AND detected_at > datetime('now', '-7 days')
        ORDER BY quality_score DESC
        LIMIT 10
    """)

    opportunities = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({
        'opportunities': opportunities,
        'total': len(opportunities),
        'high_quality': sum(1 for o in opportunities if o['quality_score'] >= 0.9),
    })


@social_manager_bp.route('/comments', methods=['GET'])
def get_pending_comments():
    """Get generated comments awaiting publication."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, title, opportunity_type, comment_text, quality_score
        FROM social_opportunities
        WHERE comment_generated = 1
        AND published_at IS NULL
        ORDER BY quality_score DESC
        LIMIT 10
    """)

    comments = [dict(row) for row in cursor.fetchall()]
    db.close()

    return jsonify({
        'pending_comments': comments,
        'total': len(comments),
        'ready_to_post': sum(1 for c in comments if c['quality_score'] >= 0.85),
    })


@social_manager_bp.route('/comments/<int:comment_id>/publish', methods=['POST'])
def publish_comment(comment_id: int):
    """Publish a comment to LinkedIn."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE social_opportunities
        SET published_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (comment_id,))

    db.commit()
    db.close()

    logger.info(f"Comment {comment_id} published")

    return jsonify({'status': 'published', 'comment_id': comment_id})


@social_manager_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get social manager statistics."""
    db = get_db()
    cursor = db.cursor()

    # Weekly themes created vs approved
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN founder_approved = 1 THEN 1 END) as approved
        FROM weekly_themes
        WHERE created_at > datetime('now', '-30 days')
    """)
    themes_stats = dict(cursor.fetchone())

    # Opportunities detected
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN comment_generated = 1 THEN 1 END) as comments_generated
        FROM social_opportunities
        WHERE detected_at > datetime('now', '-30 days')
    """)
    opp_stats = dict(cursor.fetchone())

    # Comments published
    cursor.execute("""
        SELECT COUNT(*) as published FROM social_opportunities
        WHERE published_at > datetime('now', '-30 days')
    """)
    published_count = cursor.fetchone()['published']

    db.close()

    return jsonify({
        'themes': themes_stats,
        'opportunities': opp_stats,
        'comments_published': published_count,
        'period': 'last_30_days',
        'generated_at': datetime.now().isoformat(),
    })


@social_manager_bp.route('/health', methods=['GET'])
def health():
    """Health check."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM weekly_themes LIMIT 1")
        db.close()
        return jsonify({'status': 'healthy'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
