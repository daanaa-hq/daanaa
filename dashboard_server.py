#!/usr/bin/env python3
"""
Daanaa President Dashboard Server
Run this on home server to serve the dashboard on WiFi
"""

import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Dashboard data file (edit this in JSON format)
DATA_FILE = Path("/home/akbar/meritgiving/dashboard_data.json")

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.serve_dashboard()
        elif self.path == "/api/data":
            self.serve_data()
        else:
            super().do_GET()

    def serve_dashboard(self):
        """Serve the main HTML dashboard"""
        html = load_dashboard_html()
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_data(self):
        """Serve the dashboard data as JSON"""
        if DATA_FILE.exists():
            data = DATA_FILE.read_text()
        else:
            data = "{}"
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(data.encode())

    def log_message(self, format, *args):
        """Quiet logging"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

def load_dashboard_html():
    """Load and serve the dashboard HTML"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daanaa — President Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #333;
            padding: 0;
            min-height: 100vh;
        }
        header {
            background: #0f3460;
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        header h1 { font-size: 24px; margin-bottom: 5px; }
        header p { font-size: 12px; opacity: 0.8; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #e74c3c;
        }
        .card.warning { border-left-color: #f39c12; }
        .card.success { border-left-color: #27ae60; }
        .card.info { border-left-color: #3498db; }
        .card h2 { font-size: 18px; margin-bottom: 12px; color: #0f3460; }
        .card h3 { font-size: 14px; color: #555; margin: 12px 0 8px 0; }
        .card p { font-size: 13px; line-height: 1.6; color: #666; margin-bottom: 8px; }
        .card ul { margin-left: 20px; font-size: 13px; }
        .card li { margin-bottom: 6px; color: #666; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin-right: 8px;
        }
        .badge.urgent { background: #e74c3c; color: white; }
        .badge.high { background: #f39c12; color: white; }
        .badge.medium { background: #3498db; color: white; }
        .badge.done { background: #27ae60; color: white; }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
            font-size: 13px;
        }
        .metric:last-child { border: none; }
        .metric-value { font-weight: bold; color: #0f3460; }
        .action {
            background: #ecf0f1;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
            font-size: 13px;
            border-left: 3px solid #e74c3c;
        }
        .action.complete { border-left-color: #27ae60; background: #d5f4e6; }
        .time { font-size: 12px; color: #999; }
        footer {
            text-align: center;
            padding: 20px;
            color: #bdc3c7;
            font-size: 12px;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 40px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            header h1 { font-size: 20px; }
            .card { padding: 15px; }
        }
    </style>
</head>
<body>
    <header>
        <h1>🚀 Daanaa President Dashboard</h1>
        <p>Real-time operations overview | Last updated: <span id="timestamp">loading...</span></p>
    </header>

    <div class="container">
        <!-- URGENT THIS WEEK -->
        <div class="grid">
            <div class="card">
                <h2>
                    <span class="badge urgent">🔴 URGENT</span>
                    This Week (Jun 15–21)
                </h2>
                <div class="action">
                    <strong>1. Attorney Engagement</strong>
                    <p>Identify nonprofit + tech attorney; send G1 packet</p>
                    <p class="time">Due: Jun 21 | Owner: You</p>
                </div>
                <div class="action">
                    <strong>2. Master Narrative Edit</strong>
                    <p>Edit voice, budget ($X–$Y), team details</p>
                    <p class="time">Due: Jun 21 | Owner: You</p>
                </div>
                <div class="action">
                    <strong>3. Funder Deadlines</strong>
                    <p>Verify exact dates for Fast Forward, Knight, Mozilla</p>
                    <p class="time">Due: Jun 21 | Owner: You</p>
                </div>
                <div class="action">
                    <strong>4. Fiscal Sponsor Research</strong>
                    <p>ID 2–3 candidates (Fast Forward, Tides, TECHSoup)</p>
                    <p class="time">Due: Jun 21 | Owner: You</p>
                </div>
            </div>

            <!-- KEY METRICS -->
            <div class="card info">
                <h2>📊 Key Metrics</h2>
                <div class="metric">
                    <span>Grant Applications</span>
                    <span class="metric-value">0 / 15</span>
                </div>
                <div class="metric">
                    <span>Funding Approved</span>
                    <span class="metric-value">$0 / $500K</span>
                </div>
                <div class="metric">
                    <span>Partner Applications</span>
                    <span class="metric-value">TBD</span>
                </div>
                <div class="metric">
                    <span>Nonprofits Claimed</span>
                    <span class="metric-value">~500K / 1.87M</span>
                </div>
                <div class="metric">
                    <span>Days Until First Decision</span>
                    <span class="metric-value">61 days</span>
                </div>
            </div>
        </div>

        <!-- NEXT WEEK -->
        <div class="grid">
            <div class="card warning">
                <h2>
                    <span class="badge high">🟡 HIGH PRIORITY</span>
                    Next Week (Jun 22–28)
                </h2>
                <div class="action">
                    <strong>Attorney Feedback</strong>
                    <p>3 critical questions answered (entity, solicitation, GPO)</p>
                </div>
                <div class="action">
                    <strong>Application Tracker Setup</strong>
                    <p>Copy to Google Sheets; fill in all 15 funders</p>
                </div>
                <div class="action">
                    <strong>Growth Tooling Finish</strong>
                    <p>Uptime Kuma admin setup + Plausible docker config</p>
                </div>
            </div>

            <!-- BLOCKERS -->
            <div class="card">
                <h2>⚠️ What's Blocking You</h2>
                <h3>Missing Attorney Info</h3>
                <p>Can't finalize legal narratives without attorney name + G1 answers</p>
                <h3>Budget Not Set</h3>
                <p>Master narrative incomplete; all 15 adaptations waiting on your number</p>
                <h3>Deadline Verification</h3>
                <p>Can't submit without confirmed funder deadlines</p>
                <h3>Server Access</h3>
                <p>Uptime Kuma + Plausible pending your config (2–3 min total)</p>
            </div>
        </div>

        <!-- ACTIVE WORKSTREAMS -->
        <div class="card success">
            <h2>✅ Active Workstreams (Status)</h2>
            <h3>G0: Funding Pipeline</h3>
            <ul>
                <li>Attorney engagement — 🔴 BLOCKED (waiting on you)</li>
                <li>Narrative adaptations — ✅ 15/15 DRAFTED</li>
                <li>Application tracker — 🔴 BLOCKED (needs your setup)</li>
                <li>Funder submissions — 🟡 READY (Jul 5 target)</li>
                <li>First decision — 🟠 TIMELINE (Aug 15 target)</li>
            </ul>
            <h3>Product: Retention Features (G2)</h3>
            <ul>
                <li>One-click giving — 📋 SPEC DONE (engineering)</li>
                <li>Org donation links — 📋 SPEC DONE (engineering)</li>
                <li>Nonprofit claiming — 📋 SPEC DONE (engineering)</li>
                <li>Every.org integration — 🔴 BLOCKED (partnership TBD)</li>
            </ul>
            <h3>Growth Tooling</h3>
            <ul>
                <li>Uptime Kuma — 🔴 BLOCKED (your 2-min setup)</li>
                <li>Plausible — 🔴 BLOCKED (your docker config)</li>
                <li>Axe-core a11y — ✅ LIVE</li>
                <li>Satori OG — ✅ LIVE</li>
            </ul>
        </div>

        <!-- WEEKLY RITUAL -->
        <div class="grid">
            <div class="card">
                <h2>📅 Weekly Friday Update (5 min)</h2>
                <p style="margin-bottom: 12px;">Copy this Friday EOD and send back to me:</p>
                <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                    <p>## Week of [Jun 22–28]</p>
                    <p>Attorney: ☐ YES ☐ NO</p>
                    <p>Budget: ☐ LOCKED ☐ TBD</p>
                    <p>Blockers resolved: [list]</p>
                    <p>New blockers: [list]</p>
                    <p>Next week priority: [top 1 thing]</p>
                </div>
            </div>

            <div class="card">
                <h2>🔗 Important Links</h2>
                <p><strong>Docs:</strong></p>
                <ul>
                    <li><code>/docs/PRESIDENT_DASHBOARD.md</code></li>
                    <li><code>/docs/G0_APPLICATION_TRACKER.md</code></li>
                    <li><code>/docs/G0_DEADLINE_CALENDAR.md</code></li>
                </ul>
                <p><strong>Server:</strong></p>
                <ul>
                    <li>This dashboard: <code>192.168.1.73:8000</code></li>
                    <li>Uptime Kuma: <code>192.168.1.73:3101</code></li>
                    <li>API: <code>localhost:5000</code></li>
                </ul>
            </div>
        </div>

        <!-- DAILY BRIEFING -->
        <div class="card info">
            <h2>☀️ Daily Briefing (Read This Morning)</h2>
            <p><strong>Check these 3 things every morning (2 min):</strong></p>
            <h3>1. What's Due Today?</h3>
            <p>Look at "URGENT This Week" section above. Anything due today?</p>
            <h3>2. Any Funder/Attorney Messages?</h3>
            <p>Check email for attorney replies or funder inquiries. Update dashboard if changes.</p>
            <h3>3. What's the One Thing?</h3>
            <p>What's the #1 thing you're doing today? Make sure it's on the blockers list.</p>
        </div>

        <footer>
            <p>Daanaa President Dashboard v1.0 | Last sync: <span id="footer-time">loading</span></p>
            <p>Questions? Check the docs folder or ask your partner in crime.</p>
        </footer>
    </div>

    <script>
        // Update timestamps
        function updateTime() {
            const now = new Date().toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            document.getElementById('timestamp').textContent = now;
            document.getElementById('footer-time').textContent = now;
        }
        updateTime();
        setInterval(updateTime, 60000);

        // Load data if available
        fetch('/api/data')
            .then(r => r.json())
            .catch(() => ({}))
            .then(data => console.log('Dashboard data loaded'));
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Create dashboard data file if it doesn't exist
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({
            "last_updated": datetime.now().isoformat(),
            "attorney": {"name": "", "email": "", "status": "blocked"},
            "budget": {"ask": "", "status": "blocked"},
            "funder_deadlines": {"verified": 0, "total": 15}
        }, indent=2))

    # Start server
    server = HTTPServer(("0.0.0.0", 8000), DashboardHandler)
    print(f"\n✅ Daanaa President Dashboard running")
    print(f"📱 Access on WiFi: http://192.168.1.73:8000")
    print(f"🔌 Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Dashboard stopped")
