# Performance Review

## Confirmed optimizations

- The droplet search backend keeps a persistent SQLite connection per worker and uses `PRAGMA mmap_size` and `cache_size`.
- Search uses FTS5 and semantic lookup.
- The frontend uses debounced search and explicit request timeouts.

## Likely inefficiencies

- The codebase carries multiple representations of similar concepts, which likely increases both UI and pipeline maintenance cost.
- The repo contains large generated artifacts and historical files, so broad scans or syncs can be expensive.
- Some enrichment and model-assisted jobs appear to be batch-oriented and may need careful scheduling to avoid contention.

