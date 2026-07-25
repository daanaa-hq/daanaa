#!/usr/bin/env python3
"""
Website search blitz efficiency tracker — phase-aware.
Monitors discovery and link extraction throughput every 2 hours.
Detects phase transitions automatically.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path.home() / 'meritgiving/data/merit_registry.db'
LOG_DIR = Path.home() / 'meritgiving/logs'
STATE_FILE = LOG_DIR / '.blitz_state.json'
ALERT_FILE = LOG_DIR / 'blitz_efficiency_alert.log'

def load_state():
    """Load previous checkpoint."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'websites': 0, 'donate_links': 0, 'timestamp': None, 'phase': 'discovery'}

def save_state(state):
    """Save current checkpoint."""
    STATE_FILE.write_text(json.dumps(state))

def get_discovery_counts():
    """Get current discovery progress."""
    conn = sqlite3.connect(str(DB))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
    websites = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL")
    donate_links = cursor.fetchone()[0]
    
    conn.close()
    return websites, donate_links

def detect_phase(delta_sites, delta_links):
    """Detect current pipeline phase."""
    if delta_sites > delta_links * 2:
        return 'discovery'
    elif delta_links > 0:
        return 'link_extraction'
    else:
        return 'processing'

def main():
    now = datetime.now()
    prev_state = load_state()
    websites, donate_links = get_discovery_counts()
    
    # Calculate deltas
    delta_websites = websites - prev_state.get('websites', websites)
    delta_links = donate_links - prev_state.get('donate_links', donate_links)
    
    # Throughput per 2-hour interval
    sites_per_hour = (delta_websites / 2.0) if delta_websites > 0 else 0
    links_per_hour = (delta_links / 2.0) if delta_links > 0 else 0
    
    # Detect phase
    phase = detect_phase(delta_websites, delta_links)
    phase_change = " ⏭️ PHASE CHANGE" if phase != prev_state.get('phase', 'discovery') else ""
    
    # Efficiency depends on phase
    if phase == 'discovery':
        efficiency = min(100, (sites_per_hour / 500.0) * 100)  # Target: 500 sites/h
        primary_metric = f"Sites: {delta_websites:+6d}/2h ({sites_per_hour:6.0f}/h)"
    else:
        efficiency = min(100, (links_per_hour / 100.0) * 100)  # Target: 100 links/h
        primary_metric = f"Links: {delta_links:+6d}/2h ({links_per_hour:6.0f}/h)"
    
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    status = "✓"
    
    log_line = (
        f"[{ts}] {status} Phase: {phase:17s} | {primary_metric:30s} | "
        f"Efficiency: {efficiency:5.1f}%{phase_change}"
    )
    
    print(log_line)
    
    # Log to file
    with open(LOG_DIR / 'blitz_efficiency.log', 'a') as f:
        f.write(log_line + '\n')
    
    # Only alert on severe drop within same phase
    if efficiency < 30:
        alert = f"[{ts}] ⚠️  SEVERE DROP: {efficiency:.1f}% efficiency in {phase} phase. Check process.\n"
        with open(ALERT_FILE, 'a') as f:
            f.write(alert)
        print(alert, end='')
    
    # Save state for next iteration
    save_state({
        'websites': websites,
        'donate_links': donate_links,
        'timestamp': ts,
        'efficiency': efficiency,
        'phase': phase,
    })

if __name__ == '__main__':
    main()
