"""
Daanaa Campaign Management API
Manages carousel creation, approval, scheduling, and analytics
Local-first, no external APIs
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import sqlite3
import hashlib
import os
from urllib.parse import urlencode

campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/api/campaigns')

# Database schema (will be created on init)
CAMPAIGNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    carousel_type TEXT,
    status TEXT DEFAULT 'draft',
    content JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_by TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP,
    scheduled_for TIMESTAMP,
    posted_at TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS campaign_analytics (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    metric_type TEXT,
    metric_value INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE TABLE IF NOT EXISTS utm_links (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    base_url TEXT,
    full_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);
"""

def get_db():
    """Get database connection"""
    db_path = '/home/akbar/meritgiving/data/merit_registry.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_campaigns_db():
    """Initialize campaigns tables"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript(CAMPAIGNS_SCHEMA)
    conn.commit()
    conn.close()

def generate_campaign_id():
    """Generate unique campaign ID"""
    timestamp = datetime.now().isoformat()
    hash_obj = hashlib.md5(timestamp.encode())
    return f"camp_{hash_obj.hexdigest()[:12]}"

def generate_utm_link(base_url, campaign_id, campaign_title):
    """Generate UTM-tagged link"""
    utm_params = {
        'utm_source': 'linkedin',
        'utm_medium': 'social',
        'utm_campaign': campaign_id,
        'utm_content': campaign_title.lower().replace(' ', '_')
    }
    full_url = f"{base_url}?{urlencode(utm_params)}"
    return full_url

# Routes

@campaigns_bp.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'campaigns_api'})

@campaigns_bp.route('/create', methods=['POST'])
def create_campaign():
    """Create a new campaign draft"""
    data = request.json
    campaign_id = generate_campaign_id()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO campaigns (id, title, carousel_type, content, status, submitted_by)
        VALUES (?, ?, ?, ?, 'draft', ?)
    """, (
        campaign_id,
        data.get('title'),
        data.get('carousel_type'),
        json.dumps(data.get('content', {})),
        data.get('submitted_by', 'system')
    ))

    conn.commit()
    conn.close()

    return jsonify({
        'id': campaign_id,
        'status': 'draft',
        'created_at': datetime.now().isoformat()
    }), 201

@campaigns_bp.route('/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get campaign details"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Campaign not found'}), 404

    campaign = dict(row)
    campaign['content'] = json.loads(campaign['content'])
    return jsonify(campaign)

@campaigns_bp.route('/<campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Update campaign (draft only)"""
    data = request.json

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE campaigns
        SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'draft'
    """, (
        data.get('title'),
        json.dumps(data.get('content', {})),
        campaign_id
    ))

    conn.commit()
    conn.close()

    return jsonify({'id': campaign_id, 'status': 'updated'})

@campaigns_bp.route('/batch/list', methods=['GET'])
def list_campaigns():
    """List campaigns (filtered by status)"""
    status = request.args.get('status', 'draft')
    limit = request.args.get('limit', 50, type=int)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, status, created_at, approved_at, scheduled_for
        FROM campaigns
        WHERE status = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (status, limit))

    campaigns = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'campaigns': campaigns, 'count': len(campaigns)})

@campaigns_bp.route('/<campaign_id>/submit-for-approval', methods=['POST'])
def submit_for_approval(campaign_id):
    """Submit draft for approval"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE campaigns
        SET status = 'pending_approval', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (campaign_id,))

    conn.commit()
    conn.close()

    return jsonify({'id': campaign_id, 'status': 'pending_approval'})

@campaigns_bp.route('/<campaign_id>/approve', methods=['POST'])
def approve_campaign(campaign_id):
    """Approve campaign for scheduling"""
    data = request.json
    approved_by = data.get('approved_by', 'admin')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE campaigns
        SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (approved_by, campaign_id))

    conn.commit()
    conn.close()

    return jsonify({'id': campaign_id, 'status': 'approved'})

@campaigns_bp.route('/<campaign_id>/schedule', methods=['POST'])
def schedule_campaign(campaign_id):
    """Schedule campaign for posting"""
    data = request.json
    scheduled_for = data.get('scheduled_for')  # ISO format datetime

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE campaigns
        SET status = 'scheduled', scheduled_for = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'approved'
    """, (scheduled_for, campaign_id))

    conn.commit()

    # Generate UTM link
    campaign = get_campaign(campaign_id)
    utm_link = generate_utm_link(
        'https://daanaa.org/directory',
        campaign_id,
        campaign.json['title']
    )

    cursor.execute("""
        INSERT INTO utm_links (id, campaign_id, utm_source, utm_medium, utm_campaign, utm_content, base_url, full_url)
        VALUES (?, ?, 'linkedin', 'social', ?, ?, 'https://daanaa.org/directory', ?)
    """, (
        f"{campaign_id}_utm",
        campaign_id,
        campaign_id,
        campaign.json['title'].lower().replace(' ', '_'),
        utm_link
    ))

    conn.commit()
    conn.close()

    return jsonify({
        'id': campaign_id,
        'status': 'scheduled',
        'scheduled_for': scheduled_for,
        'utm_link': utm_link
    })

@campaigns_bp.route('/<campaign_id>/record-metric', methods=['POST'])
def record_metric(campaign_id):
    """Record engagement metric (likes, comments, clicks)"""
    data = request.json
    metric_type = data.get('metric_type')  # impressions, likes, comments, shares, clicks
    metric_value = data.get('metric_value', 1)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO campaign_analytics (id, campaign_id, metric_type, metric_value)
        VALUES (?, ?, ?, ?)
    """, (
        f"{campaign_id}_{metric_type}_{datetime.now().timestamp()}",
        campaign_id,
        metric_type,
        metric_value
    ))

    conn.commit()
    conn.close()

    return jsonify({'recorded': True})

@campaigns_bp.route('/<campaign_id>/analytics', methods=['GET'])
def get_analytics(campaign_id):
    """Get campaign analytics summary"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT metric_type, SUM(metric_value) as total
        FROM campaign_analytics
        WHERE campaign_id = ?
        GROUP BY metric_type
    """, (campaign_id,))

    metrics = {row['metric_type']: row['total'] for row in cursor.fetchall()}

    # Get UTM link
    cursor.execute("""
        SELECT full_url FROM utm_links WHERE campaign_id = ?
    """, (campaign_id,))

    utm_row = cursor.fetchone()
    utm_link = utm_row['full_url'] if utm_row else None

    conn.close()

    return jsonify({
        'campaign_id': campaign_id,
        'metrics': metrics,
        'utm_link': utm_link
    })

@campaigns_bp.route('/dashboard/weekly-summary', methods=['GET'])
def weekly_summary():
    """Get weekly performance summary"""
    week_ago = datetime.now() - timedelta(days=7)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.title,
            COUNT(DISTINCT a.metric_type) as metric_types,
            SUM(CASE WHEN a.metric_type = 'impressions' THEN a.metric_value ELSE 0 END) as impressions,
            SUM(CASE WHEN a.metric_type = 'likes' THEN a.metric_value ELSE 0 END) as likes,
            SUM(CASE WHEN a.metric_type = 'clicks' THEN a.metric_value ELSE 0 END) as clicks,
            c.posted_at
        FROM campaigns c
        LEFT JOIN campaign_analytics a ON c.id = a.campaign_id
        WHERE c.posted_at > ? AND c.status = 'posted'
        GROUP BY c.id
        ORDER BY c.posted_at DESC
    """, (week_ago,))

    campaigns = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({'weekly_campaigns': campaigns})

# Initialize on import
init_campaigns_db()
