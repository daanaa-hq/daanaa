"""
STREAM 7 Issue 4: Admin Key Verification
Ensures admin endpoints are protected by env-var-only keys (never hardcoded)
"""
import os
import hashlib
import time
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class AdminKeyValidator:
    """Validates admin API keys from environment only"""
    
    def __init__(self):
        """Load admin key from DAANAA_ADMIN_KEY env var (never from code or config)"""
        self.admin_key = os.environ.get('DAANAA_ADMIN_KEY')
        
        if not self.admin_key:
            logger.warning("⚠️  DAANAA_ADMIN_KEY not set. Admin endpoints will reject all requests.")
            self.admin_key = None
        else:
            # Log only hash, never the actual key
            key_hash = hashlib.sha256(self.admin_key.encode()).hexdigest()[:8]
            logger.info(f"✓ Admin key loaded (hash: {key_hash}...)")
        
        # Track failed attempts to prevent brute force
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_seconds = 300  # 5 minutes
    
    def validate_admin_key(self, provided_key: str, client_id: str) -> Tuple[bool, str]:
        """
        Validate provided admin key
        
        Returns: (is_valid, message)
        """
        if not self.admin_key:
            return False, "Admin key not configured on server"
        
        # Check if client is locked out
        if client_id in self.failed_attempts:
            attempts, last_time = self.failed_attempts[client_id]
            if attempts >= self.max_attempts:
                if time.time() - last_time < self.lockout_seconds:
                    return False, f"Too many attempts. Try again in {int(self.lockout_seconds - (time.time() - last_time))} seconds"
                else:
                    # Lockout expired
                    del self.failed_attempts[client_id]
        
        # Validate key using constant-time comparison (prevent timing attacks)
        if self._constant_time_compare(provided_key, self.admin_key):
            logger.info(f"✓ Admin key valid for {client_id}")
            # Clear failed attempts on success
            if client_id in self.failed_attempts:
                del self.failed_attempts[client_id]
            return True, "Admin key valid"
        else:
            # Log failed attempt
            if client_id not in self.failed_attempts:
                self.failed_attempts[client_id] = [0, time.time()]
            
            attempts, _ = self.failed_attempts[client_id]
            attempts += 1
            self.failed_attempts[client_id] = [attempts, time.time()]
            
            remaining = self.max_attempts - attempts
            logger.warning(f"❌ Invalid admin key from {client_id} ({remaining} attempts left)")
            
            if attempts >= self.max_attempts:
                return False, f"Too many failed attempts. Account locked for {self.lockout_seconds} seconds"
            else:
                return False, f"Invalid admin key. {remaining} attempt(s) remaining"
    
    @staticmethod
    def _constant_time_compare(a: str, b: str) -> bool:
        """
        Compare two strings in constant time to prevent timing attacks
        """
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def extract_admin_key_from_header(self, headers: dict) -> Optional[str]:
        """Extract admin key from request headers"""
        # Check X-Admin-Key header
        key = headers.get('X-Admin-Key')
        if key:
            return key
        
        # Check Authorization header (Bearer token)
        auth = headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        
        return None

# Global instance
_validator = AdminKeyValidator()

def validate_admin_request(headers: dict, client_id: str) -> Tuple[bool, str]:
    """Wrapper for Flask endpoint protection"""
    key = _validator.extract_admin_key_from_header(headers)
    
    if not key:
        return False, "Missing admin key in X-Admin-Key header or Authorization: Bearer"
    
    return _validator.validate_admin_key(key, client_id)

if __name__ == '__main__':
    # Test without env var
    if 'DAANAA_ADMIN_KEY' in os.environ:
        del os.environ['DAANAA_ADMIN_KEY']
    
    validator = AdminKeyValidator()
    valid, msg = validator.validate_admin_key("test", "client1")
    assert not valid, "Should fail without env var"
    print(f"✓ Rejects request without env var: {msg}")
    
    # Test with env var
    os.environ['DAANAA_ADMIN_KEY'] = "super_secret_key_12345"
    validator = AdminKeyValidator()
    
    # Valid key
    valid, msg = validator.validate_admin_key("super_secret_key_12345", "client1")
    assert valid, "Valid key should pass"
    print(f"✓ Accepts valid key: {msg}")
    
    # Invalid key
    valid, msg = validator.validate_admin_key("wrong_key", "client1")
    assert not valid, "Invalid key should fail"
    print(f"✓ Rejects invalid key: {msg}")
    
    # Brute force attempt
    for i in range(5):
        valid, msg = validator.validate_admin_key("wrong_key", "brute_client")
    
    # 6th attempt should be locked
    valid, msg = validator.validate_admin_key("wrong_key", "brute_client")
    assert not valid and "locked" in msg.lower(), "Should lock after 5 attempts"
    print(f"✓ Brute force protection: {msg}")
    
    print("\n✅ Admin key validation tests passed")
