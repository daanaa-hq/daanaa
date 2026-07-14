# AI Governance Review

Date: 2026-07-13

## Current AI Uses Found

- Mission generation and categorization from public records.
- Embeddings and semantic search.
- Concierge draft preparation from public information.
- Possible AI validation language in vendor/rating code comments.
- Agent workflows, institutional review, visibility generation, and internal drafting.

## Strengths

- `STEWARDSHIP.md` states AI is a tool, not a replacement for responsibility.
- Concierge disclosure standard is explicit in `daanaa_api.py` and board records.
- AI is framed as infrastructure that may be unobtrusive but not deceptive.
- Local inference is preferred for private or batch work.
- Deterministic scoring is not AI-generated.

## Gaps

| Gap | Severity | Evidence |
|---|---:|---|
| Concierge tests currently fail in combined targeted run. | Medium | `tests/test_concierge_confirm.py` schema drift. |
| AI-assisted labels are not proven uniform across all public surfaces. | Medium | Multiple frontend/data paths. |
| "AI with empathy" is mostly principle/copy, not yet measured behavior. | Medium | Library 004 and service docs. |
| External AI prohibition for Tier 2 data needs stronger machine enforcement. | High | Library 011 vs `privacy_check.sh`. |

## Governing Standard

AI may be unobtrusive, but never deceptively hidden. The person or organization affected by AI-assisted output must have a correction path and, where consequence is material, a source trail.

## Recommended Controls

- Add an AI output register: feature, model/source, input tier, output tier, disclosure, correction path, owner.
- Add tests for AI-disclosure strings on public AI-generated content.
- Add Tier 2 external-AI scanning to privacy checks.
- Use human accountability language in public docs, not "the AI decided" framing.

