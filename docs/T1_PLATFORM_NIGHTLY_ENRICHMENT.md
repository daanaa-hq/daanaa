# T1 Platform — Nightly Enrichment Team

**Vision:** A coordinated team of agents running every night (21:00–~09:00) on local
server hardware (Ryzen 9700X + R9700 32GB), continuously enriching the nonprofit
database: websites → donate links → missions → tags → refreshed search.

**Orchestrator:** `scripts/gpu_night.sh` (cron `start` 21:00, `stop` 09:00).
It is the single entry point — it launches every night worker below and kills
them all in `stop()`. There is no separate Python orchestrator (one was built
2026-06-10 and deleted the same day — it duplicated this stack; see LESSONS.md).

---

## The Team (launched by `gpu_night.sh start`)

| Worker | Script | Resource | What it does |
|--------|--------|----------|--------------|
| Embed server | `embed_server.sh` (:11436) | GPU | mxbai-embed-large — verification + re-embeds |
| Mission model | llama-server (:11437) | GPU | Mission generation model, 6 slots, cont. batching |
| Storyteller | `generate_missions.py` then `generate_missions_irs_bmf.py` (6 workers) | GPU via :11437 | AI missions: standard scope first, then the 245K IRS_BMF backlog (batch 20/call, EIN-validated writes, resumable) |
| Payment hunter | `cpu_night.sh` → `donation_link_pipeline.py` | CPU + net | Loops Phase 1 (discover 200) + Phase 2 (release ≤50 verified ≥90 conf) all night |
| Website hunter | `web_night.sh` → `web_finder_agent.py` | CPU + :11436 | Loops 200-org passes, revenue DESC; domain-pattern candidates verified by GPU embeddings (≥0.85); finds marked `beta`, failures marked `no_website_found` (90-day retry) |
| Re-embedder | `reembed_watchdog.py` | GPU via :11436 | Re-embeds orgs whose mission changed (threshold 5000) |

## Supporting cron (separate entries, already aligned)

| Time | Job | Purpose |
|------|-----|---------|
| 22:00 | `batch_enrichment_scheduler.py` | ProPublica backfill (2K/night) |
| 02:15 | `run_agents.py --agent quality` | Data quality checks |
| 02:35 | `run_agents.py --agent cause_tags` | 3–5 cause tags per org (qwen2.5:7b via Ollama) |
| 02:30 | `overnight_pipeline.py` | Revocation check, manual submissions, ProPublica, v4 scorer |
| 03:00 | `sync_irs_revocations.py` | Daily revoked-org removal (the "list refresh") |
| 07:00 | `detect_data_changes.sh` | Detects major changes → flags redeploy |
| 07:30 | `build_fts_index.py --rebuild` | FTS refresh (~25s) so new missions are searchable |
| 09:00 | `gpu_night.sh stop` | Tear down GPU night workers |
| 09:05 | `gpu_night.sh stop_embed_server` | Release embed server |

**Priority order:** every queue (websites, donate links, missions) is consumed
revenue DESC, so the highest-impact gaps fill first. Revoked orgs are removed
daily before anything publishes.

---

## Models (local only — no cloud for batch ML)

| Task | Model | Where |
|------|-------|-------|
| Missions | Qwen3-30B-A3B-Instruct-2507 Q4_K_M (MoE, 3B active — switched from dense 32B 2026-06-10 after 11K-mission supervised run, ~7 orgs/sec) | llama-server :11437, Vulkan1 |
| Embeddings | mxbai-embed-large | llama-server :11436 (Ollama :11434 fallback) |
| Cause tags | qwen2.5:7b | Ollama :11434 |

VRAM budget (32GB): mission model ~17–19G + embed ~1G + tags 7B ~5G — all three
fit concurrently.

---

## Stewardship rules enforced (unchanged)

1. No bypass of bot protection (CAPTCHA, Cloudflare, robots.txt)
2. 403/429 → domain blocked 30 days
3. Donate links fail closed: publish only at ≥90 confidence
4. Web-discovered sites marked `beta` until human-reviewed (disclosure policy)
5. Mission source always attributed (`ai_ntee`, `ai_web`, `ai_generated`)
6. Revoked orgs filtered before publish

## Success metrics (3-month targets)

| Metric | Current (2026-06-10) | Target |
|--------|----------------------|--------|
| Verified donate links | 234 | 1,000 |
| Websites discovered | — | 10K new |
| Missions generated | — | 100K |

---

**Owner:** T1 Platform · **Updated:** 2026-06-10
