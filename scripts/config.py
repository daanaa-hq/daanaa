"""
Configuration management for discovery daemon.
All timeouts and parameters read from environment or defaults.
Validates at startup, fails fast on bad config.
"""
import os
import sys

def get_discovery_timeout():
    """Get batch timeout from env var or default to 600s"""
    timeout_str = os.getenv('DISCOVERY_BATCH_TIMEOUT', '600')
    try:
        timeout = int(timeout_str)
        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")
        return timeout
    except ValueError as e:
        print(f"ERROR: Invalid DISCOVERY_BATCH_TIMEOUT: {e}", file=sys.stderr)
        sys.exit(1)

def get_worker_count():
    """Get worker count from env var or default to 32"""
    workers_str = os.getenv('DISCOVERY_WORKERS', '32')
    try:
        workers = int(workers_str)
        if workers <= 0 or workers > 128:
            raise ValueError(f"Workers must be 1-128, got {workers}")
        return workers
    except ValueError as e:
        print(f"ERROR: Invalid DISCOVERY_WORKERS: {e}", file=sys.stderr)
        sys.exit(1)

def get_batch_size():
    """Get batch size from env var or default to 1000"""
    size_str = os.getenv('DISCOVERY_BATCH_SIZE', '1000')
    try:
        size = int(size_str)
        if size <= 0 or size > 10000:
            raise ValueError(f"Batch size must be 1-10000, got {size}")
        return size
    except ValueError as e:
        print(f"ERROR: Invalid DISCOVERY_BATCH_SIZE: {e}", file=sys.stderr)
        sys.exit(1)

def validate_config():
    """Validate all config at startup, fail fast if invalid"""
    try:
        timeout = get_discovery_timeout()
        workers = get_worker_count()
        batch = get_batch_size()
        return {
            'timeout': timeout,
            'workers': workers,
            'batch_size': batch
        }
    except SystemExit:
        raise

if __name__ == '__main__':
    config = validate_config()
    print("✓ Config valid:")
    for key, val in config.items():
        print(f"  {key}: {val}")
