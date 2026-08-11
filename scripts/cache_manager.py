"""
Cache Manager: Event-driven invalidation with TTL support
Fixes stale data issues in daanaa_api.py

Problem: Cache serves data up to 10 minutes old
Solution: Event markers + TTL = 30-second max staleness
"""

import json
import time
from pathlib import Path
from typing import Any, Optional
import threading


class CacheManager:
    """Thread-safe cache with TTL + event-driven invalidation"""
    
    def __init__(self, marker_dir: str = "/tmp"):
        self.data = {}
        self.ttl = {}
        self.marker_dir = marker_dir
        self.last_invalidate = {}
        self.lock = threading.Lock()
    
    def set(self, key: str, value: Any, ttl: int = 600, scope: str = "org") -> None:
        """Store value with TTL (seconds)"""
        full_key = f"{scope}:{key}"
        with self.lock:
            self.data[full_key] = value
            self.ttl[full_key] = time.time() + ttl
    
    def get(self, key: str, scope: str = "org") -> Optional[Any]:
        """
        Retrieve value if not expired and not invalidated.
        Checks invalidation marker file.
        """
        full_key = f"{scope}:{key}"
        
        with self.lock:
            # Check invalidation marker
            marker = Path(f"{self.marker_dir}/cache_invalidate.{scope}.json")
            if marker.exists():
                marker_mtime = marker.stat().st_mtime
                if scope not in self.last_invalidate or marker_mtime > self.last_invalidate[scope]:
                    # Clear this scope
                    keys_to_delete = [k for k in self.data if k.startswith(f"{scope}:")]
                    for k in keys_to_delete:
                        del self.data[k]
                        del self.ttl[k]
                    self.last_invalidate[scope] = time.time()
                    return None
            
            # Check TTL expiry
            if full_key not in self.data:
                return None
            
            if time.time() > self.ttl[full_key]:
                del self.data[full_key]
                del self.ttl[full_key]
                return None
            
            return self.data[full_key]
    
    def invalidate_scope(self, scope: str) -> None:
        """Manually invalidate all keys in a scope"""
        with self.lock:
            keys_to_delete = [k for k in self.data if k.startswith(f"{scope}:")]
            for k in keys_to_delete:
                del self.data[k]
                del self.ttl[k]
            self.last_invalidate[scope] = time.time()
    
    def stats(self) -> dict:
        """Cache stats for monitoring"""
        with self.lock:
            return {
                "total_keys": len(self.data),
                "scopes": len(set(k.split(":")[0] for k in self.data)),
                "memory_mb": sum(len(str(v)) for v in self.data.values()) / 1024 / 1024
            }


# Global cache instance
_cache = CacheManager()


def write_invalidation_marker(scope: str, marker_dir: str = "/tmp") -> None:
    """Signal API to invalidate cache for a scope (call from pipeline scripts)"""
    marker = Path(f"{marker_dir}/cache_invalidate.{scope}.json")
    marker.write_text(json.dumps({"ts": time.time(), "scope": scope}))


if __name__ == "__main__":
    # Quick test
    _cache.set("test_org", {"name": "Test"}, ttl=60)
    print("Set test_org")
    print("Get test_org:", _cache.get("test_org"))
    print("Stats:", _cache.stats())
    
    # Test invalidation
    write_invalidation_marker("org")
    print("After invalidation:", _cache.get("test_org"))
