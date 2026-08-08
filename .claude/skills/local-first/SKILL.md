---
name: local-first
description: Use when a task involves bulk or repetitive text work (classification, summarization, extraction, triage, embeddings, draft generation) over many records - routes it to the local GPU instead of burning frontier-model tokens. Also use when asked to reduce token usage or speed up throughput.
---

# Local-first inference

Daanaa owns a 32GB-VRAM GPU that sits idle most of the time. Every bulk text task
run through a frontier model is money and latency spent on work this box does for
free, at 95-167 tok/s.

**The rule: if the task is repetitive, high-volume, and quality-tolerant, it goes
local. If it needs judgment across the repository, it stays here.**

## How to call it

```python
import sys; sys.path.insert(0, "scripts")
from lib.local_llm import chat, embed, health, AGENT, FAST

chat("Classify this mission into one NTEE letter: ...", model=AGENT, max_tokens=8)
embed("some text")            # 1024-dim, mxbai-embed-large
health()                      # which services are reachable
```

Never hardcode `127.0.0.1:11437` or `:11436`. Those dedicated servers are gone;
llama-swap on `:8080` replaced them. Hardcoded ports are exactly how twelve
scripts came to be silently pointing at dead services while the GPU idled (see
`scripts/lib/local_llm.py` header).

## Route locally

- Classifying, tagging, or bucketing many records (cause tags, NTEE assignment)
- Summarizing or rewriting per-record text (missions, descriptions)
- Extracting fields from fetched HTML
- Embeddings of any volume
- First-pass triage where a human or frontier model reviews the output
- Drafting boilerplate that will be edited before it ships

## Keep here (do NOT route locally)

- Anything requiring repository-wide context or cross-file reasoning
- Security, privacy, methodology, or public-claim decisions
- Work whose output ships to users without review
- Debugging that depends on reading real code and history

A 30B model is a good worker and a poor architect. Routing judgment work to it to
save tokens produces confident, wrong output that costs more to unpick than it saved.

## Models

| Slot | Model | Use |
|---|---|---|
| `agent` / `analysis` / `code` | Qwen3-30B-A3B-Instruct Q4_K_M | default for real work |
| `fast` | Mistral-7B-Instruct Q4_K_M | trivial high-volume only |

Qwen3-30B-A3B is Mixture-of-Experts: ~30B total, ~3B active per token. That is why
it is both the best-quality and one of the fastest options that fits this card.
It occupies ~20.4GB of ~32GB VRAM. llama-swap keeps one model resident and unloads
on idle, so do not start competing llama-server instances -- they will fight for VRAM.

Cold start is ~25s (17GB read from disk). Warm calls are sub-second. For batches,
send the whole batch in one run rather than spacing calls out, so the model stays
resident.

## Privacy (non-negotiable)

Local inference is how Daanaa keeps its promise that individual user data never
reaches a hosted model (Stewardship P2, PRIVACY-INVARIANTS). `local_llm.py`
deliberately has **no cloud fallback** — a silent failover would convert a
local-only guarantee into an unreviewed network call. If local inference is down,
the correct behaviour is to fail and say so, not to reroute.

## Before a long batch

Check `nvidia-smi`/`rocm-smi` headroom and confirm nothing else holds the GPU.
The GPU is shared with the enrichment pipeline; two large jobs at once will swap
and crawl. `health()` tells you what is loaded.
