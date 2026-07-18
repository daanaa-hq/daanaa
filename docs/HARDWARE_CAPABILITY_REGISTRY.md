# Hardware Capability Registry

Validation date: 2026-07-18. This is a partial, honest registry: sandboxed
telemetry commands were not all available, so unknown values remain unknown.

| Capability | Observed value | Confidence |
|---|---|---|
| OS/runtime | Linux; Python virtualenv and Node project present | medium |
| Local model | Ollama `mxbai-embed-large:latest`, 669 MB | high |
| GPU | not validated in this cycle | low |
| CPU/RAM/storage telemetry | not validated in this cycle | low |
| Supported safe tasks | embeddings, local retrieval; other tasks require benchmark | medium |
| Fallback | deterministic code, then manual review | high |
| External AI | none approved for restricted data | high |

Revalidate after material hardware, runtime, model, or workload changes. Do not
claim throughput, power, or latency until a local benchmark records them.
