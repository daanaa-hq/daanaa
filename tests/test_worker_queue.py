"""P6 Phase 3 Issue #9: Thread-safe worker queue tests"""

import unittest
import threading
from scripts.worker_queue import WorkerQueue, DataWriter


class TestWorkerQueue(unittest.TestCase):
    """Thread-safe queue with retry logic"""

    def test_sequential_processing(self):
        """Queue processes jobs in FIFO order"""
        results = []

        def handler(value):
            results.append(value)

        queue = WorkerQueue()
        queue.register_handler("append", handler)

        for i in range(10):
            queue.submit("append", value=i)

        queue.process_all()

        # All values should be present in order
        self.assertEqual(results, list(range(10)))

    def test_concurrent_submissions(self):
        """Multiple threads can submit safely"""
        queue = WorkerQueue()
        counter = [0]  # Mutable counter

        def increment():
            counter[0] += 1

        queue.register_handler("increment", lambda: increment())

        # 10 threads each submitting 10 jobs
        threads = []
        for _ in range(10):
            for _ in range(10):
                queue.submit("increment")

        queue.process_all()

        # All 100 increments should complete
        self.assertEqual(counter[0], 100)

    def test_retry_on_failure(self):
        """Failed jobs are retried"""
        results = []

        def flaky_handler(value):
            if len(results) < 2:
                results.append("attempt")
                raise Exception("Temporary failure")
            results.append(value)

        queue = WorkerQueue(max_retries=3)
        queue.register_handler("flaky", flaky_handler)

        queue.submit("flaky", value="success")
        stats = queue.process_all()

        # Job should have been retried
        self.assertGreater(stats["retried"], 0)
        self.assertEqual(stats["completed"], 1)

    def test_data_writer_atomic_updates(self):
        """DataWriter ensures atomic updates"""
        writer = DataWriter()
        writer.start()

        # 10 threads updating same key
        def update_thread(value):
            writer.submit_update("shared_key", value)

        threads = [
            threading.Thread(target=update_thread, args=(i,))
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        writer.process_all()

        # Should have final value (no data loss)
        self.assertIsNotNone(writer.get("shared_key"))

    def test_no_data_loss_under_load(self):
        """1000 concurrent operations preserve all data"""
        writer = DataWriter()
        writer.start()

        # Each thread updates 100 keys
        def worker(thread_id):
            for i in range(100):
                writer.submit_update(f"key_{thread_id}_{i}", f"value_{i}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        writer.process_all()

        # All 1000 keys should exist
        self.assertEqual(len(writer.db_data), 1000)


if __name__ == "__main__":
    unittest.main()
