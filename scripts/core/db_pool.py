"""
P6 Phase 3 Issue #7: Database connection pooling wrapper
Quick integration for daanaa_api.py
"""

import queue
import sqlite3
from pathlib import Path

class ConnectionPool:
    """Pool of persistent SQLite connections with <1ms checkout time"""
    
    def __init__(self, db_path, pool_size=5, timeout=30):
        self.db_path = db_path
        self.pool = queue.Queue(maxsize=pool_size)
        self.timeout = timeout
        
        # Pre-populate pool
        for _ in range(pool_size):
            conn = sqlite3.connect(str(db_path), timeout=timeout, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self.pool.put(conn)
    
    def get_connection(self):
        """Checkout a connection (blocking if none available)"""
        try:
            return self.pool.get(timeout=1)
        except queue.Empty:
            # Fallback: create fresh connection
            return sqlite3.connect(str(self.db_path), timeout=self.timeout, check_same_thread=False)
    
    def return_connection(self, conn):
        """Return connection to pool"""
        try:
            self.pool.put_nowait(conn)
        except queue.Full:
            conn.close()  # Pool full, discard
    
    def close_all(self):
        """Close all pooled connections"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except queue.Empty:
                break

# Usage in daanaa_api.py:
#   from db_pool import ConnectionPool
#   _db_pool = ConnectionPool(DB_PATH, pool_size=5)
#   
#   # Replace: db = sqlite3.connect(DB_PATH, ...)
#   # With:    db = _db_pool.get_connection()
#   # And:     _db_pool.return_connection(db)  # in finally block
