# Enrichment — Missions & Embeddings

## Canonical Files

### Missions
- **`missions/generate_missions.py`** — AI mission generation (uses local Qwen3-30B via llama.cpp, port 11437)
- **`enrich_cause_tags_mission.py`** — Cause tag extraction + linking to missions

### Embeddings
- **`embeddings/build_org_embeddings.py`** — Generate mxbai-embed vectors for semantic search (via llama.cpp, port 11436)
- **`embeddings/embedding_extraction.py`** — Extract + validate embeddings

## How To...

**Generate missions for new orgs:**
```bash
# Runs automatically via overnight_pipeline.py
# Manual run:
python3 scripts/enrichment/missions/generate_missions.py
```

**Build embeddings:**
```bash
# Runs automatically via overnight_pipeline.py
# Manual run:
python3 scripts/enrichment/embeddings/build_org_embeddings.py
```

**Monitor local inference servers:**
```bash
# Check Qwen3-30B (mission generation)
curl -s http://localhost:11437/v1/models | jq .

# Check mxbai-embed (embeddings)
curl -s http://localhost:11436/v1/models | jq .

# Both should return 200 with model info
```

## Hardware Requirements

**Server:** Ryzen 9700X + R9700 32GB VRAM (ROCm 6.4)

**Models in use:**
- `Qwen3-30B-A3B-Instruct-2507-Q4_K_M` — Mission generation (port 11437, 6-worker parallelization)
- `mxbai-embed-large-v1` — Embeddings (port 11436)

**Off-peak only:** GPU is night-only (10pm–6am) for heat management.

## Database Schema

**Input:** `registry_enriched` (org_name, NTEE, location)
**Output:** Updated columns:
- `mission` — 1-2 sentence AI-generated description
- `mission_source` — `ai_ntee`, `ai_generated`, or scraped
- `cause_tags` — JSON array of categorization tags
- `org_embeddings` table — Vectors for semantic search (mxbai-embed-large)

## Do Not Use

- Cloud LLM APIs (use local inference only)
- `generate_missions_haiku.py` (wrong model, too small)
- `legacy_embedding_*.py` (superseded)

## Recent Changes

- 2026-08-12: Task #2 cause alias expansion (added 14 new cause categories, 169 total synonyms)
- 2026-07-26: Cause tag coverage gap identified (data-dark small orgs still need manual tags)
- 2026-07-12: Qwen mission generation tuned for quality (better adherence to "1-2 sentences")

## Testing

```bash
# Verify embeddings work
python3 -c "
import sqlite3
conn = sqlite3.connect('data/merit_registry.db')
count = conn.execute('SELECT COUNT(*) FROM org_embeddings').fetchone()[0]
print(f'Embeddings available: {count:,} orgs')
"

# Semantic search test
python3 << 'EOF'
import sqlite3
import numpy as np
conn = sqlite3.connect('data/merit_registry.db')

# Get query embedding
query_vec = np.random.rand(1024)  # Placeholder (real implementation loads from llama.cpp)
# Find nearest orgs (cosine similarity)
results = conn.execute('''
  SELECT rowid, org_name FROM org_embeddings 
  ORDER BY similarity DESC LIMIT 5
''').fetchall()
print("Top 5 similar orgs:", results)
EOF
```

## Troubleshooting

**Mission generation is slow (>30min)?**
→ Check GPU: `radeontop` (see if GPU is utilized)
→ Check Qwen server: `curl http://localhost:11437/v1/models`
→ Restart: `pkill -f llama-server` then `./start_llama_server.sh`

**Embeddings incomplete?**
→ Restart embedding server: `pkill -f "embed" && ./start_embed_server.sh`
→ Check coverage: Count in `org_embeddings` table should be ~2.05M

**Mission text is bad quality?**
→ Tweak prompt in `generate_missions.py` (line where mission prompt is defined)
→ Re-run generation for sample of 100 orgs to test
→ Validate with human spot-check before full rebuild

## See Also

- `docs/ENRICHMENT_RUNBOOK.md` — Enrichment operating notes
- `scripts/enrichment/build_ntee_cause_tags.py` — Cause-tag generation utility
- This README’s Missions and Embeddings sections are the current local navigation; dedicated subdirectory READMEs are not yet built.
