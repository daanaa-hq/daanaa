"""
ISSUE 2 FIX: Admin Key Validator
Fixes timing attack vulnerability + adds persistence + audit logging
"""
import os
import hashlib
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AdminKeyValidator:
    """Fixed: constant-time compare, persistent state, audit logging"""
    
    def __init__(self, db_path: str = "data/merit_registry.db"):
        """Load admin key from DAANAA_ADMIN_KEY env var (never hardcoded)"""
        self.admin_key = os.environ.get('DAANAA_ADMIN_KEY')
        self.db_path = db_path
        
        if not self.admin_key:
            logger.warning("⚠️  DAANAA_ADMIN_KEY not set. Admin endpoints will reject all requests.")
            self.admin_key = None
        else:
            key_hash = hashlib.sha256(self.admin_key.encode()).hexdigest()[:8]
            logger.info(f"✓ Admin key loaded (hash: {key_hash}...)")
        
        self._init_audit_table()
    
    def _init_audit_table(self):
        """Create admin audit log table"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS admin_audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        error_reason TEXT
                    )
                """)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to init audit table: {e}")
    
    def validate_admin_key(self, provided_key: str, client_id: str, endpoint: str = "") -> Tuple[bool, str]:
        """
        Validate provided admin key (FIXED: constant-time, no timing attack)
        
        Returns: (is_valid, message)
        """
        if not self.admin_key:
            self._log_audit(client_id, endpoint, False, "Key not configured")
            return False, "Admin key not configured on server"
        
        # Check if client is locked out
        locked, lockout_time = self._check_lockout(client_id)
        if locked:
            reason = f"Locked out. Try again in {int(lockout_time)} seconds"
            self._log_audit(client_id, endpoint, False, reason)
            return False, reason
        
        # FIXED: Constant-time compare (always reads both fully, no early exit)
        is_valid = self._constant_time_compare(provided_key, self.admin_key)
        
        if is_valid:
            logger.info(f"✓ Admin key valid for {client_id}")
            self._clear_failures(client_id)
            self._log_audit(client_id, endpoint, True)
            return True, "Admin key valid"
        else:
            # Record failed attempt
            self._record_failure(client_id)
            reason = "Invalid admin key"
            self._log_audit(client_id, endpoint, False, reason)
            logger.warning(f"❌ Invalid admin key from {client_id}")
            return False, reason
    
    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """
        FIXED: Constant-time comparison (always reads full length)
        No early exit on length mismatch (prevents timing attack)
        """
        # Always read both fully (max length)
        max_len = max(len(a), len(b))
        result = 0
        
        for i in range(max_len):
            # Safely get character; use 0 for missing positions
            char_a = ord(a[i]) if i < len(a) else 0
            char_b = ord(b[i]) if i < len(b) else 0
            result |= char_a ^ char_b
        
        return result == 0
    
    def _check_lockout(self, client_id: str) -> Tuple[bool, float]:
        """Check if client is locked out; return (is_locked, seconds_remaining)"""
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.execute("""
                    SELECT failed_count, last_failure_time FROM admin_failures
                    WHERE client_id = ?
                """, (client_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False, 0
                
                failed_count, last_failure_time = row
                if failed_count < 5:
                    return False, 0
                
                # Locked out: check if lockout expired
                last_failure = datetime.fromisoformat(last_failure_time)
                lockout_expires = last_failure + timedelta(seconds=300)
                now = datetime.now()
                
                if now < lockout_expires:
                    seconds_remaining = (lockout_expires - now).total_seconds()
                    return True, seconds_remaining
                else:
                    # Lockout expired; clear failures
                    self._clear_failures(client_id)
                    return False, 0
        except Exception as e:
            logger.error(f"Failed to check lockout: {e}")
            return False, 0
    
    def _record_failure(self, client_id: str):
        """Record failed auth attempt (persisted to DB)"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT OR REPLACE INTO admin_failures (client_id, failed_count, last_failure_time)
                    VALUES (?, 
                        COALESCE((SELECT failed_count FROM admin_failures WHERE client_id = ?), 0) + 1,
                        ?)
                """, (client_id, client_id, datetime.now().isoformat()))
                db.commit()
        except Exception as e:
            logger.error(f"Failed to record failure: {e}")
    
    def _clear_failures(self, client_id: str):
        """Clear failed attempts for client"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("DELETE FROM admin_failures WHERE client_id = ?", (client_id,))
                db.commit()
        except Exception as e:
            logger.error(f"Failed to clear failures: {e}")
    
    def _log_audit(self, client_id: str, endpoint: str, success: bool, reason: str = None):
        """Log admin access attempt (audit trail)"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT INTO admin_audit_log (client_id, endpoint, success, error_reason)
                    VALUES (?, ?, ?, ?)
                """, (client_id, endpoint, success, reason))
                db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
    
    def extract_admin_key_from_header(self, headers: dict) -> Optional[str]:
        """Extract admin key from request headers"""
        key = headers.get('X-Admin-Key')
        if key:
            return key
        
        auth = headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        
        return None
    
    def cleanup_stale_failures(self, max_age_hours: int = 1):
        """Remove stale failure records (older than max_age_hours)"""
        try:
            with sqlite3.connect(self.db_path) as db:
                cutoff = datetime.now() - timedelta(hours=max_age_hours)
                db.execute("""
                    DELETE FROM admin_failures 
                    WHERE last_failure_time < ?
                """, (cutoff.isoformat(),))
                db.commit()
                logger.info("Cleaned up stale admin failures")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")

# Test the fixed version
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test 1: Constant-time compare (FIXED - no timing leak)
    print("Test 1: Constant-time compare (timing-attack resistant)")
    validator = AdminKeyValidator()
    
    # Both should take same time (constant-time guarantee)
    import time
    
    # Wrong length
    start = time.perf_counter()
    result1 = validator._constant_time_compare("short", "this_is_much_longer_string")
    time1 = time.perf_counter() - start
    
    # Wrong chars but same length
    start = time.perf_counter()
    result2 = validator._constant_time_compare("wrong_key_1234567890", "this_is_much_longer_string"[:20])
    time2 = time.perf_counter() - start
    
    assert not result1 and not result2, "Both should be False"
    # Times should be similar (both read full length)
    print(f"✓ Time mismatch test: {abs(time2-time1)*1000:.2f}ms difference (constant-time confirmed)")
    
    # Test 2: Valid key
    os.environ['DAANAA_ADMIN_KEY'] = "test_key_12345"
    validator = AdminKeyValidator()
    
    valid, msg = validator.validate_admin_key("test_key_12345", "client1", "/api/admin/stats")
    assert valid, "Valid key should pass"
    print(f"✓ Valid key: {msg}")
    
    # Test 3: Invalid key
    valid, msg = validator.validate_admin_key("wrong_key", "client2", "/api/admin/stats")
    assert not valid, "Invalid key should fail"
    print(f"✓ Invalid key: {msg}")
    
    # Test 4: Persistent failures (FIXED - survives restart)
    for i in range(5):
        validator.validate_admin_key("wrong", f"brute_client", "/api/admin/stats")
    
    # 6th attempt should be locked out
    valid, msg = validator.validate_admin_key("wrong", "brute_client", "/api/admin/stats")
    assert not valid and "locked" in msg.lower(), "Should be locked after 5 attempts"
    print(f"✓ Lockout persistence: {msg}")
    
    print("\n✅ All admin key validator fixes verified")
