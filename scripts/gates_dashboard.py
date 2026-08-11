#!/usr/bin/env python3
"""
Gates Execution Dashboard - Local WiFi Access
Runs on http://192.168.1.73:9000
Shows: Task status, daemon health, GPU load, recent work
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Gates configuration
GATES = {
    0: {"name": "Operational Stability", "status": "monitoring", "hours": "72h (1 day done)"},
    1: {"name": "Verification Integrity", "status": "pending", "hours": "10h (Aug 12-23)"},
    3: {"name": "Search Quality Audit", "status": "pending", "hours": "72h (starts Aug 11)"},
    4: {"name": "Website Verification", "status": "blocked", "hours": "4h (depends on Gate 3)"},
    5: {"name": "Small Org Fairness", "status": "blocked", "hours": "6h (depends on Gates 3-4)"},
    6: {"name": "Explanation Completeness", "status": "blocked", "hours": "8h (depends on Gates 3-4)"},
    7: {"name": "Independence Verification", "status": "pending", "hours": "2h (parallel)"},
    8: {"name": "Comprehensive Discovery", "status": "blocked", "hours": "20h (depends on all)"},
}

def get_daemon_health():
    """Read daemon health from /tmp/daemon_health.json"""
    health_files = [
        "/tmp/discovery_daemon.health.json",
        "/tmp/inference_server.health.json",
        "/tmp/api.health.json",
    ]

    health = {}
    for f in health_files:
        if Path(f).exists():
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    health[Path(f).stem] = data.get("status", "unknown")
            except:
                health[Path(f).stem] = "error reading"
    return health

def get_gpu_utilization():
    """Get R9700 GPU load"""
    try:
        result = subprocess.run(
            ["rocm-smi", "--load"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse GPU load from rocm-smi output
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return lines[1].split()[-1] if lines[1] else "N/A"
    except:
        pass
    return "N/A"

def get_recent_commits():
    """Get last 5 git commits"""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            cwd="/home/akbar/meritgiving",
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
    except:
        pass
    return []

def get_disk_space():
    """Get disk usage"""
    try:
        result = subprocess.run(
            ["df", "-h", "/home/akbar"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    "total": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": parts[4]
                }
    except:
        pass
    return {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Daanaa Gates Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            font-size: 2em;
            margin-bottom: 10px;
            color: #fff;
        }
        .subtitle {
            color: #888;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .refresh-hint {
            color: #666;
            font-size: 0.85em;
            margin-bottom: 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #2a2a3e;
            border: 1px solid #404050;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        .card h2 {
            font-size: 1.1em;
            margin-bottom: 15px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-pending { background: #4a7c59; color: #fff; }
        .status-in-progress { background: #5d8aa8; color: #fff; }
        .status-blocked { background: #8b4040; color: #fff; }
        .status-pass { background: #4a9b5c; color: #fff; }
        .status-fail { background: #c74040; color: #fff; }
        .status-monitoring { background: #8b6f47; color: #fff; }

        .gate-list {
            list-style: none;
        }
        .gate-item {
            padding: 10px 0;
            border-bottom: 1px solid #404050;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .gate-item:last-child {
            border-bottom: none;
        }
        .gate-num {
            font-weight: bold;
            color: #7fb3d5;
            min-width: 30px;
        }
        .gate-name {
            flex: 1;
            margin-left: 10px;
        }
        .gate-hours {
            color: #888;
            font-size: 0.9em;
        }

        .health-item {
            padding: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .health-status {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .health-healthy { background: #4a9b5c; color: #fff; }
        .health-unhealthy { background: #c74040; color: #fff; }
        .health-unknown { background: #666; color: #fff; }

        .commits-list {
            font-family: monospace;
            font-size: 0.85em;
            line-height: 1.5;
            color: #7fb3d5;
        }
        .commits-list li {
            list-style: none;
            padding: 4px 0;
            border-bottom: 1px solid #404050;
        }
        .commits-list li:last-child {
            border-bottom: none;
        }

        .stat-row {
            padding: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stat-label {
            color: #888;
        }
        .stat-value {
            font-weight: bold;
            color: #fff;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #404050;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #7fb3d5, #5d8aa8);
            width: var(--percent);
            transition: width 0.3s ease;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Daanaa Gates Execution</h1>
        <p class="subtitle">Evolution Framework • Aug 10 - Sept 30</p>
        <p class="refresh-hint">⟲ Auto-refreshes every 30s</p>

        <div class="grid">
            <!-- Gates Status -->
            <div class="card full-width">
                <h2>🎯 Gate Progression</h2>
                <ul class="gate-list">
                    <li class="gate-item">
                        <span class="gate-num">0</span>
                        <span class="gate-name">Operational Stability</span>
                        <span class="status-badge status-monitoring">Monitoring</span>
                        <span class="gate-hours">72h (1d done)</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">1</span>
                        <span class="gate-name">Verification Integrity + P6 Phase 2</span>
                        <span class="status-badge status-pending">Pending</span>
                        <span class="gate-hours">10h</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">3</span>
                        <span class="gate-name">Search Quality Audit</span>
                        <span class="status-badge status-pending">Pending</span>
                        <span class="gate-hours">72h (starts tomorrow)</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">4</span>
                        <span class="gate-name">Website Verification</span>
                        <span class="status-badge status-blocked">Blocked</span>
                        <span class="gate-hours">4h</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">5</span>
                        <span class="gate-name">Small Org Fairness</span>
                        <span class="status-badge status-blocked">Blocked</span>
                        <span class="gate-hours">6h</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">6</span>
                        <span class="gate-name">Explanation Completeness</span>
                        <span class="status-badge status-blocked">Blocked</span>
                        <span class="gate-hours">8h</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">7</span>
                        <span class="gate-name">Independence Verification</span>
                        <span class="status-badge status-pending">Pending</span>
                        <span class="gate-hours">2h (parallel)</span>
                    </li>
                    <li class="gate-item">
                        <span class="gate-num">8</span>
                        <span class="gate-name">Comprehensive Discovery</span>
                        <span class="status-badge status-blocked">Blocked</span>
                        <span class="gate-hours">20h</span>
                    </li>
                </ul>
            </div>

            <!-- Daemon Health -->
            <div class="card">
                <h2>🔧 System Health</h2>
                <div id="daemon-health">Loading...</div>
            </div>

            <!-- GPU Utilization -->
            <div class="card">
                <h2>🎮 GPU (R9700)</h2>
                <div id="gpu-info">Loading...</div>
            </div>

            <!-- Disk Space -->
            <div class="card">
                <h2>💾 Storage</h2>
                <div id="disk-info">Loading...</div>
            </div>

            <!-- Recent Work -->
            <div class="card full-width">
                <h2>📝 Recent Commits</h2>
                <ul class="commits-list" id="commits">
                    <li>Loading...</li>
                </ul>
            </div>

            <!-- Parallel Streams -->
            <div class="card full-width">
                <h2>⚡ Parallel Streams</h2>
                <div class="stat-row">
                    <span class="stat-label">P6 Phase 2 Fixes</span>
                    <span class="status-badge status-pending">Pending</span>
                    <span class="stat-value">10h (6 issues)</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">GPU Night Work</span>
                    <span class="status-badge status-in-progress">Active</span>
                    <span class="stat-value">8h/night (10pm-6am)</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Documentation</span>
                    <span class="status-badge status-in-progress">Active</span>
                    <span class="stat-value">Ongoing</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                // Update daemon health
                if (data.daemon_health) {
                    const health = data.daemon_health;
                    let html = '';
                    for (const [name, status] of Object.entries(health)) {
                        const cls = status === 'healthy' ? 'health-healthy' :
                                   status === 'unhealthy' ? 'health-unhealthy' : 'health-unknown';
                        html += `<div class="health-item"><span>${name}</span><span class="health-status ${cls}">${status}</span></div>`;
                    }
                    document.getElementById('daemon-health').innerHTML = html || '<p>No daemons detected</p>';
                }

                // Update GPU utilization
                if (data.gpu_load) {
                    document.getElementById('gpu-info').innerHTML =
                        `<div class="stat-row"><span class="stat-label">Load</span><span class="stat-value">${data.gpu_load}</span></div>
                         <div class="progress-bar"><div class="progress-fill" style="--percent: ${data.gpu_load}"></div></div>
                         <p style="color: #888; font-size: 0.85em; margin-top: 10px;">Active 10pm-6am</p>`;
                }

                // Update disk info
                if (data.disk_space) {
                    const disk = data.disk_space;
                    const percent = parseInt(disk.percent);
                    document.getElementById('disk-info').innerHTML =
                        `<div class="stat-row"><span class="stat-label">Used</span><span class="stat-value">${disk.used} / ${disk.total}</span></div>
                         <div class="progress-bar"><div class="progress-fill" style="--percent: ${percent}%"></div></div>
                         <div class="stat-row" style="margin-top: 10px;"><span class="stat-label">Available</span><span class="stat-value">${disk.available}</span></div>`;
                }

                // Update commits
                if (data.commits && data.commits.length > 0) {
                    document.getElementById('commits').innerHTML =
                        data.commits.map(c => `<li>${c}</li>`).join('');
                }
            } catch (e) {
                console.error('Dashboard update error:', e);
            }
        }

        // Initial load
        updateDashboard();

        // Refresh every 30s
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    return jsonify({
        "daemon_health": get_daemon_health(),
        "gpu_load": get_gpu_utilization(),
        "disk_space": get_disk_space(),
        "commits": get_recent_commits(),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Gates Dashboard starting on http://192.168.1.73:9000")
    print("📱 Access from any WiFi device")
    print("⟲ Auto-refreshes every 30s")
    app.run(host='0.0.0.0', port=9000, debug=False)
