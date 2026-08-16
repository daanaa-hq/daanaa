"""
STREAM 7 Issue 2: Rate Limiting - Prevents scraping and DDoS
Protects all API endpoints with token bucket algorithm
"""
import time
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        capacity: max tokens
        refill_rate: tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed, False if rate-limited."""
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self):
        # Rate limits per endpoint
        self.limits = {
            '/api/organizations': (100, 1),      # 100 per second
            '/api/search': (50, 1),               # 50 per second
            '/api/org/': (200, 1),                # 200 per second
            '/api/ntee': (50, 1),                 # 50 per second
            '/api/claims': (20, 1),               # 20 per second (sensitive)
            '/api/admin': (10, 1),                # 10 per second (admin)
        }
        self.buckets = defaultdict(lambda: {})  # {client_id: {endpoint: TokenBucket}}
    
    def get_client_id(self, request_headers: dict) -> str:
        """Extract client ID from request (IP + User-Agent hash)"""
        ip = request_headers.get('X-Forwarded-For', request_headers.get('Remote-Addr', '0.0.0.0'))
        ua = request_headers.get('User-Agent', 'unknown')
        return hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()[:16]
    
    def is_rate_limited(self, client_id: str, endpoint: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if client is rate-limited on endpoint
        
        Returns: (is_limited, metadata)
        """
        # Get limit for endpoint (default: 60 req/sec)
        if endpoint not in self.limits:
            for pattern, limit in self.limits.items():
                if endpoint.startswith(pattern.rstrip('/')):
                    capacity, refill_rate = limit
                    break
            else:
                capacity, refill_rate = (60, 1)
        else:
            capacity, refill_rate = self.limits[endpoint]
        
        # Get or create bucket for this client+endpoint
        if endpoint not in self.buckets[client_id]:
            self.buckets[client_id][endpoint] = TokenBucket(capacity, refill_rate)
        
        bucket = self.buckets[client_id][endpoint]
        
        # Try to consume token
        if bucket.consume():
            logger.debug(f"✓ {client_id} → {endpoint} (allowed)")
            return False, {"limit": capacity, "remaining": int(bucket.tokens)}
        else:
            logger.warning(f"⚠️  {client_id} → {endpoint} (rate-limited)")
            # Calculate reset time
            reset_in = (1 - bucket.tokens) / bucket.refill_rate
            return True, {
                "limit": capacity,
                "remaining": 0,
                "reset_in_seconds": int(reset_in) + 1,
                "retry_after": int(time.time()) + int(reset_in) + 1
            }
    
    def cleanup_stale_clients(self, max_age_hours: int = 1):
        """Remove buckets for inactive clients"""
        # Simple cleanup: remove if last_refill is old
        # In production: use persistent cache with Redis
        now = time.time()
        stale_clients = []
        
        for client_id, endpoints in self.buckets.items():
            for endpoint, bucket in endpoints.items():
                age_hours = (now - bucket.last_refill) / 3600
                if age_hours > max_age_hours:
                    stale_clients.append(client_id)
                    break
        
        for client_id in stale_clients:
            del self.buckets[client_id]
            logger.info(f"Cleaned up stale client: {client_id}")

# Global instance
_rate_limiter = RateLimiter()

def check_rate_limit(client_id: str, endpoint: str) -> Tuple[bool, dict]:
    """Wrapper for use in Flask"""
    return _rate_limiter.is_rate_limited(client_id, endpoint)

def rate_limit_key(request_headers: dict) -> str:
    """Get rate limit key from request headers"""
    return _rate_limiter.get_client_id(request_headers)

if __name__ == '__main__':
    # Test rate limiting
    limiter = RateLimiter()
    
    # Simulate client hitting endpoint
    client = "test_client"
    endpoint = "/api/search"
    
    # First 50 should pass
    for i in range(50):
        is_limited, meta = limiter.is_rate_limited(client, endpoint)
        assert not is_limited, f"Failed at request {i}"
    
    print(f"✓ First 50 requests allowed")
    
    # 51st should be rate-limited
    is_limited, meta = limiter.is_rate_limited(client, endpoint)
    assert is_limited, "Should be rate-limited at 51st request"
    print(f"✓ 51st request rate-limited: {meta['retry_after']}")
    
    print("✅ Rate limiter tests passed")
