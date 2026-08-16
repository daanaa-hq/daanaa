"""P6 Phase 3 Issue #8: Cache invalidation tests"""

import unittest
import time
import json
from pathlib import Path
from scripts.core.cache_manager import CacheManager, write_invalidation_marker


class TestCacheInvalidation(unittest.TestCase):
    """Cache invalidation with TTL + event markers"""

    def setUp(self):
        self.cache = CacheManager(marker_dir="/tmp")

    def test_ttl_expiry(self):
        """Cache entries expire after TTL"""
        self.cache.set("test", "value", ttl=1)
        self.assertIsNotNone(self.cache.get("test"))

        time.sleep(1.1)
        self.assertIsNone(self.cache.get("test"))

    def test_marker_invalidation(self):
        """Marker file triggers cache invalidation"""
        self.cache.set("org:123", "old_value")
        self.assertIsNotNone(self.cache.get("org:123"))

        # Write marker
        write_invalidation_marker("org")

        # Should be cleared
        self.assertIsNone(self.cache.get("org:123"))

        # Cleanup
        Path("/tmp/cache_invalidate.org.json").unlink(missing_ok=True)

    def test_selective_scope_invalidation(self):
        """Only invalidate specific scope"""
        self.cache.set("123", "org_value", scope="org")
        self.cache.set("search_term", "search_value", scope="search")

        self.cache.invalidate_scope("org")

        self.assertIsNone(self.cache.get("123", scope="org"))
        self.assertIsNotNone(self.cache.get("search_term", scope="search"))

    def test_concurrent_access(self):
        """Cache handles concurrent reads/writes"""
        import threading

        def writer(i):
            self.cache.set(f"key_{i}", f"value_{i}")

        def reader(i):
            return self.cache.get(f"key_{i}")

        threads = []
        for i in range(10):
            threads.append(threading.Thread(target=writer, args=(i,)))
            threads.append(threading.Thread(target=reader, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All writes should succeed
        self.assertEqual(len(self.cache.data), 10)

    def test_stats_tracking(self):
        """Cache stats work correctly"""
        self.cache.set("org:1", "data1", scope="org")
        self.cache.set("search:term", "data2", scope="search")

        stats = self.cache.stats()
        self.assertEqual(stats["total_keys"], 2)
        self.assertEqual(stats["scopes"], 2)
        self.assertGreater(stats["memory_mb"], 0)

    def test_cache_hit_rate(self):
        """Cache serves values before expiry"""
        self.cache.set("test", "value", ttl=60)

        # Multiple reads should all hit cache
        for _ in range(100):
            result = self.cache.get("test")
            self.assertEqual(result, "value")

    def test_multiple_scopes_independent(self):
        """Different scopes don't interfere"""
        self.cache.set("123", "org_data", scope="org")
        self.cache.set("123", "search_data", scope="search")

        self.assertEqual(self.cache.get("123", scope="org"), "org_data")
        self.assertEqual(self.cache.get("123", scope="search"), "search_data")


if __name__ == "__main__":
    unittest.main()
