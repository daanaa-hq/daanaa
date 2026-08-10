"""
Frontend SPA Fallback (Flask Blueprint)

This blueprint contains ONLY the SPA fallback route.
It's registered LAST in droplet_api.py to ensure:
1. All API routes are matched first
2. Non-API requests fall through to the SPA
3. Routing is deterministic and testable
"""

from flask import Blueprint, send_from_directory
import os

frontend_bp = Blueprint('frontend', __name__)

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def serve_frontend(path):
    """Serve the React SPA — catch-all for non-API routes."""
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')
