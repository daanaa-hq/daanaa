#!/usr/bin/env python3
"""
Feedback Logger - captures every search, click, and error
"""
import json, time, os
from datetime import datetime
from collections import defaultdict

LOG_DIR = "logs/feedback"
os.makedirs(LOG_DIR, exist_ok=True)

class FeedbackLogger:
    def __init__(self):
        self.daily_file = f"{LOG_DIR}/usage_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.stats = defaultdict(int)
    
    def log_search(self, query, results_count, response_time_ms, user_ip="local"):
        entry = {
            "t": time.time(),
            "type": "search",
            "query": query,
            "results": results_count,
            "ms": response_time_ms,
            "ip": user_ip
        }
        self._write(entry)
        self.stats["searches"] += 1
        if results_count == 0:
            self.stats["zero_results"] += 1
    
    def log_profile_view(self, ein, org_name, ntee, state, percentile):
        entry = {
            "t": time.time(),
            "type": "profile_view",
            "ein": ein,
            "name": org_name,
            "ntee": ntee,
            "state": state,
            "percentile": percentile
        }
        self._write(entry)
        self.stats["profile_views"] += 1
    
    def log_error(self, error_type, details):
        entry = {
            "t": time.time(),
            "type": "error",
            "error": error_type,
            "details": str(details)
        }
        self._write(entry)
        self.stats["errors"] += 1
    
    def _write(self, entry):
        with open(self.daily_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_daily_summary(self):
        total = self.stats["searches"]
        if total == 0:
            return {"searches": 0, "zero_rate": 0, "avg_results": 0}
        
        # Calculate from file
        queries = []
        with open(self.daily_file, "r") as f:
            for line in f:
                try:
                    e = json.loads(line)
                    if e.get("type") == "search":
                        queries.append(e)
                except:
                    pass
        
        zero_rate = sum(1 for q in queries if q["results"] == 0) / len(queries) * 100 if queries else 0
        avg_results = sum(q["results"] for q in queries) / len(queries) if queries else 0
        avg_time = sum(q["ms"] for q in queries) / len(queries) if queries else 0
        
        return {
            "searches": len(queries),
            "zero_rate": round(zero_rate, 1),
            "avg_results": round(avg_results, 1),
            "avg_response_ms": round(avg_time, 1),
            "profile_views": self.stats["profile_views"],
            "errors": self.stats["errors"]
        }

logger = FeedbackLogger()
