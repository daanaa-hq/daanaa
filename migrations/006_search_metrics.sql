-- T12 Phase 1: Search metrics for zero-result analysis and pattern discovery

CREATE TABLE IF NOT EXISTS analytics_search_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day TEXT NOT NULL,
  query_length INTEGER NOT NULL,
  result_count INTEGER NOT NULL,
  zero_results INTEGER NOT NULL, -- 1 if true, 0 if false
  filters_applied INTEGER NOT NULL,
  search_mode TEXT, -- 'keyword', 'fused', 'filtered'
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(day, query_length, result_count, zero_results, filters_applied)
);

CREATE INDEX IF NOT EXISTS idx_search_metrics_day ON analytics_search_metrics(day);
CREATE INDEX IF NOT EXISTS idx_search_metrics_zero_results ON analytics_search_metrics(zero_results, day);

-- Store individual failing queries for Phase 1 analysis
CREATE TABLE IF NOT EXISTS analytics_zero_result_queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  day TEXT NOT NULL,
  query TEXT NOT NULL,
  query_length INTEGER,
  filters_applied INTEGER,
  search_mode TEXT,
  first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
  last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
  occurrence_count INTEGER DEFAULT 1,
  UNIQUE(day, query)
);

CREATE INDEX IF NOT EXISTS idx_zero_result_queries_day ON analytics_zero_result_queries(day);
CREATE INDEX IF NOT EXISTS idx_zero_result_queries_first_seen ON analytics_zero_result_queries(first_seen_at);
