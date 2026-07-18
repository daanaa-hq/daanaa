# Capability Register

| Capability | Purpose | Data access | Status | Review / rollback |
|---|---|---|---|---|
| `stewardship_core` | governance, routing, audit primitives | synthetic/local metadata only | adopted as scaffolding | revert branch commit |
| Ollama embedding model | local embeddings | only approved inputs after validation | observed, not newly activated | stop local process; no external fallback |
| Gmail OAuth | read/analyze preparation | not connected | proposed, founder approval required | disable client config |
| Calendar OAuth | event preparation | not connected | proposed, founder approval required | disable client config |

No paid or proprietary capability was introduced.
