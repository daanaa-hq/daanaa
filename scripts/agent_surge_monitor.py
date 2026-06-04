#!/usr/bin/env python3
"""
Daanaa Autonomous Agent: Surge Monitor & Relevance Mapper

Detects search query surges (3x+ baseline), classifies events, finds relevant 
orgs, and auto-boosts them in results. All actions logged and auditable.

Principles:
- Evidence-based: boosts only orgs that semantically match the surge event
- Explainable: every action logged with reasoning
- Correctable: human override available, boosts expire (TTL)
- Transparent: audit trail shows what/why/outcome
"""

import sqlite3, json, time, datetime, hashlib, sys
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# Event classification rules (can be extended)
EVENT_RULES = {
    r'hurricane|tornado|cyclone|flood|wildfire|fire|earthquake|disaster|emergency': 'disaster',
    r'homeless|homelessness|unhoused|housing crisis': 'housing',
    r'hunger|food insecurity|food bank|malnutrition': 'food',
    r'election|voting|campaign|civic engagement|registration': 'civic',
    r'layoff|recession|unemployment|economic hardship': 'employment',
    r'mental health|crisis|suicide|anxiety|depression': 'mental_health',
    r'covid|pandemic|vaccine|epidemic': 'health',
}

class Agent:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, timeout=30)
        self.db.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """Create agent tables if they don't exist."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS search_events (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                results_count INTEGER,
                clicked_ein TEXT,
                donated BOOLEAN
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS surge_detections (
                id INTEGER PRIMARY KEY,
                query TEXT NOT NULL,
                event_type TEXT,
                surge_ratio REAL,
                baseline_count INTEGER,
                surge_count INTEGER,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence REAL
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS surge_boosts (
                id INTEGER PRIMARY KEY,
                surge_id INTEGER NOT NULL,
                ein TEXT NOT NULL,
                relevance_score REAL,
                relevance_reason TEXT,
                boosted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                clicks INTEGER DEFAULT 0,
                donations INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                overridden_at DATETIME,
                override_reason TEXT,
                FOREIGN KEY(surge_id) REFERENCES surge_detections(id)
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY,
                action_type TEXT,
                action_data JSON,
                reasoning TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        """)
        
        self.db.commit()
    
    def log_action(self, action_type, action_data, reasoning):
        """Log every agent action for audit trail."""
        self.db.execute("""
            INSERT INTO agent_actions (action_type, action_data, reasoning, status)
            VALUES (?, ?, ?, 'completed')
        """, (action_type, json.dumps(action_data), reasoning))
        self.db.commit()
    
    def detect_surges(self, lookback_hours=1, surge_threshold=3.0):
        """
        Detect search query surges.

        Evidence-based: compares query count in last hour vs rolling baseline
        """
        now = datetime.datetime.now()
        lookback = now - datetime.timedelta(hours=lookback_hours)
        baseline_start = now - datetime.timedelta(hours=lookback_hours + 24)

        # Count queries in current window
        recent = self.db.execute("""
            SELECT query, COUNT(*) as count
            FROM search_events
            WHERE timestamp > ? AND timestamp <= ?
            GROUP BY query
            ORDER BY count DESC
        """, (lookback.isoformat(), now.isoformat())).fetchall()
        
        surges = []
        for row in recent:
            query = row['query']
            surge_count = row['count']
            
            # Baseline: same query in the 24-hour window before lookback
            baseline = self.db.execute("""
                SELECT COUNT(*) as count
                FROM search_events
                WHERE query = ? AND timestamp > ? AND timestamp <= ?
            """, (query, baseline_start.isoformat(), lookback.isoformat())).fetchone()['count']
            
            baseline_count = max(baseline, 1)  # Avoid division by zero
            ratio = surge_count / baseline_count
            
            if ratio >= surge_threshold:
                # Classify the event
                event_type = self._classify_event(query)
                if event_type:
                    confidence = min(ratio / 2, 1.0)  # Normalize to 0-1
                    surges.append({
                        'query': query,
                        'event_type': event_type,
                        'surge_ratio': ratio,
                        'baseline_count': baseline_count,
                        'surge_count': surge_count,
                        'confidence': confidence
                    })
                    
                    self.log_action(
                        'surge_detected',
                        {'query': query, 'ratio': ratio, 'count': surge_count},
                        f"Query '{query}' spiked {ratio:.1f}x → event type '{event_type}'"
                    )
        
        return surges
    
    def _classify_event(self, query):
        """Classify query to event type (disaster, housing, food, etc)."""
        query_lower = query.lower()
        import re
        for pattern, event_type in EVENT_RULES.items():
            if re.search(pattern, query_lower):
                return event_type
        return None
    
    def find_relevant_orgs(self, event_type, limit=20):
        """
        Find orgs semantically relevant to an event type.
        
        Evidence-based: uses cause_tags (AI-extracted from missions) as signal
        """
        orgs = self.db.execute(f"""
            SELECT EIN, organization_name, merit_score, cause_tags, 
                   is_hidden_gem, ntee1_percentile
            FROM registry_enriched
            WHERE deductibility = '1' 
              AND merit_score IS NOT NULL
              AND cause_tags LIKE ?
            ORDER BY 
              CASE WHEN is_hidden_gem = 1 THEN 0 ELSE 1 END,
              merit_score DESC
            LIMIT {limit}
        """, (f'%"{event_type}"%',)).fetchall()
        
        return [dict(o) for o in orgs]
    
    def create_boost(self, surge_id, event_type):
        """
        Create surge boosts: boost relevant orgs for this event.
        
        Boosts expire after 48 hours (event passes).
        """
        orgs = self.find_relevant_orgs(event_type, limit=20)
        
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=48)
        
        for org in orgs:
            relevance_score = 0.85 if org['is_hidden_gem'] else 0.80
            reason = f"Relevant to {event_type} event; hidden gem: {org['is_hidden_gem']}"
            
            self.db.execute("""
                INSERT INTO surge_boosts 
                (surge_id, ein, relevance_score, relevance_reason, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (surge_id, org['EIN'], relevance_score, reason, expires_at))
        
        self.db.commit()
        
        self.log_action(
            'boosts_created',
            {'surge_id': surge_id, 'event_type': event_type, 'org_count': len(orgs)},
            f"Created boosts for {len(orgs)} orgs matching '{event_type}'"
        )
    
    def run(self):
        """Main agent loop: detect → classify → boost → log."""
        print(f"[{datetime.datetime.now()}] Agent starting surge monitor...", flush=True)
        
        surges = self.detect_surges()
        
        if not surges:
            print("  No surges detected.", flush=True)
            return
        
        print(f"  Detected {len(surges)} surge(s):", flush=True)
        for surge in surges:
            print(f"    - '{surge['query']}' ({surge['event_type']}): {surge['surge_ratio']:.1f}x", flush=True)
            
            # Insert surge record
            cursor = self.db.execute("""
                INSERT INTO surge_detections 
                (query, event_type, surge_ratio, baseline_count, surge_count, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (surge['query'], surge['event_type'], surge['surge_ratio'], 
                  surge['baseline_count'], surge['surge_count'], surge['confidence']))
            self.db.commit()
            surge_id = cursor.lastrowid
            
            # Create boosts
            self.create_boost(surge_id, surge['event_type'])
            print(f"      → Boosts created (surge_id={surge_id})", flush=True)
        
        print(f"  Done. Check surge_boosts table.", flush=True)

if __name__ == '__main__':
    agent = Agent()
    agent.run()
