#!/usr/bin/env python3
"""
Telemetry API — Exposes usage patterns and adaptive UI configuration.

Endpoints:
- POST /api/telemetry/log — Log user interaction
- GET /api/telemetry/patterns — Get usage patterns summary
- GET /api/telemetry/adaptive-ui — Get current UI configuration
- POST /api/telemetry/adaptive-ui — Update UI setting
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

telemetry_bp = Blueprint('telemetry', __name__, url_prefix='/api/telemetry')

logger = logging.getLogger('telemetry_api')

# Import telemetry functions (lazy import to avoid circular dependencies)
try:
    from usage_telemetry_engine import (
        log_event,
        generate_telemetry_summary,
        get_adaptive_ui_state,
        update_adaptive_ui,
        calculate_tab_order,
        get_recommended_actions,
        get_active_hours,
    )
except ImportError:
    logger.warning("Could not import telemetry engine functions")


@telemetry_bp.route('/log', methods=['POST'])
def log_telemetry():
    """Log a user interaction event."""
    data = request.get_json()

    event_type = data.get('event_type')
    tab_name = data.get('tab_name')
    action = data.get('action')
    metadata = data.get('metadata', {})
    duration = data.get('duration_seconds')

    if not event_type:
        return jsonify({'error': 'event_type required'}), 400

    try:
        log_event(event_type, tab_name, action, metadata, duration)
        return jsonify({'status': 'logged'}), 201
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/patterns', methods=['GET'])
def get_patterns():
    """Get usage patterns and analytics."""
    try:
        summary = generate_telemetry_summary()
        tab_order = calculate_tab_order()
        actions = get_recommended_actions()
        active_hours = get_active_hours()

        return jsonify({
            'summary': summary,
            'tab_order': tab_order,
            'recommended_actions': actions,
            'active_hours': active_hours,
            'generated_at': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error generating patterns: {e}")
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/adaptive-ui', methods=['GET'])
def get_ui_config():
    """Get current adaptive UI configuration."""
    try:
        state = get_adaptive_ui_state()
        return jsonify({
            'ui_state': state,
            'generated_at': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error getting UI state: {e}")
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/adaptive-ui', methods=['POST'])
def update_ui_config():
    """Update adaptive UI configuration."""
    data = request.get_json()

    setting_name = data.get('setting_name')
    setting_value = data.get('setting_value')

    if not setting_name or not setting_value:
        return jsonify({'error': 'setting_name and setting_value required'}), 400

    try:
        update_adaptive_ui(setting_name, setting_value)
        return jsonify({'status': 'updated', 'setting': setting_name})
    except Exception as e:
        logger.error(f"Error updating UI setting: {e}")
        return jsonify({'error': str(e)}), 500


@telemetry_bp.route('/health', methods=['GET'])
def health():
    """Health check for telemetry API."""
    return jsonify({'status': 'healthy'})
