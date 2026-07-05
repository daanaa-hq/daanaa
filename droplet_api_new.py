#!/usr/bin/env python3
"""
Daanaa API — Nonprofit directory backend (Flask + SQLite)

Architecture uses Flask Blueprints for clean routing separation:
  - blueprints/api_blueprint.py       [all API routes, registered FIRST]
  - blueprints/frontend_blueprint.py  [SPA fallback, registered LAST]

This ensures API routes are ALWAYS matched before the SPA fallback.
See: ROUTING_FIX_PLAN.md
"""

import os
import sys
import logging
from datetime import datetime

# Third-party
import sentry_sdk
from flask import Flask, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Local blueprints
from blueprints.api_blueprint import api_bp, set_limiter
from blueprints.frontend_blueprint import frontend_bp

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ─── Sentry (optional) ───
_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(dsn=_sentry_dsn, send_default_pii=False)

# ─── Flask app ───
app = Flask(__name__)
CORS(app)

# ─── Rate limiting ───
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Inject limiter into api_blueprint
set_limiter(limiter)

# ─── Database ───
DB_PATH = os.environ.get("DB_PATH", 
    os.path.expanduser("~/meritgiving/data/merit_registry.db"))

# ─── Register blueprints (ORDER CRITICAL) ───
app.register_blueprint(api_bp)       # API FIRST
app.register_blueprint(frontend_bp)  # SPA LAST

# ─── Health check ───
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "db_exists": os.path.exists(DB_PATH),
        "timestamp": datetime.utcnow().isoformat()
    })

# ─── Error handlers ───
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
