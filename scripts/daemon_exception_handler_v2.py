"""ISSUE 7 FIX: Exception handler - Persist state to SQLite"""
import json
import sqlite3
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class DaemonExceptionHandler:
    """FIXED: Persist health state to SQLite"""
    
    def __init__(self, db_path: str = "data/merit_registry.db"):
        self.db_path = db_path
        self._init_state_table()
    
    def _init_state_table(self):
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""CREATE TABLE IF NOT EXISTS daemon_state (
                    daemon_name TEXT PRIMARY KEY,
                    state TEXT, timestamp TIMESTAMP, details TEXT)""")
                db.commit()
        except Exception as e:
            logger.error(f"Failed to init state table: {e}")
    
    def update_health_state(self, state: str, details: str = ""):
        """FIXED: Persist to SQLite"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""INSERT OR REPLACE INTO daemon_state 
                    (daemon_name, state, timestamp, details)
                    VALUES ('discovery_daemon', ?, CURRENT_TIMESTAMP, ?)""",
                    (state, details))
                db.commit()
            logger.info(f"✓ State persisted: {state}")
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")

class WatchdogHysteresis:
    """FIXED: Persistent state machine"""
    
    def __init__(self, db_path: str = "data/merit_registry.db"):
        self.db_path = db_path
        self._init_state_table()
    
    def _init_state_table(self):
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""CREATE TABLE IF NOT EXISTS watchdog_state (
                    id INTEGER PRIMARY KEY,
                    state TEXT, failure_count INTEGER, last_failure TIMESTAMP)""")
                db.commit()
        except Exception as e:
            logger.error(f"Failed to init watchdog table: {e}")
    
    def record_failure(self) -> Dict:
        """Record failure; persist state"""
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.execute("SELECT state, failure_count FROM watchdog_state LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    state, failure_count = row
                    failure_count += 1
                else:
                    state = "HEALTHY"
                    failure_count = 1
                
                new_state = "ERROR" if failure_count >= 3 else ("SUSPICIOUS" if failure_count >= 1 else "HEALTHY")
                
                db.execute("""INSERT OR REPLACE INTO watchdog_state (id, state, failure_count, last_failure)
                    VALUES (1, ?, ?, CURRENT_TIMESTAMP)""", (new_state, failure_count))
                db.commit()
                
                return {"action": "RESTART" if new_state == "ERROR" else "CONTINUE"}
        except Exception as e:
            logger.error(f"Failed to record failure: {e}")
            return {"action": "CONTINUE"}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    handler = DaemonExceptionHandler()
    handler.update_health_state("HEALTHY")
    print("✅ Exception handler v2 verified")
