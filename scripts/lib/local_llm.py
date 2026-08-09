"""Single source of truth for local inference endpoints.

WHY THIS EXISTS (2026-08-08)
----------------------------
Twelve-plus scripts hardcoded `http://127.0.0.1:11437` (chat) and `:11436`
(embeddings). Those dedicated llama-server instances are no longer running --
the host now uses llama-swap on :8080, which keeps ONE model resident at a time
and unloads on idle, so nothing fights over the 32GB of VRAM.

The result was silent: mission generation, cause tags, embeddings and semantic
rerank were all pointing at dead ports, and the GPU sat at 1.6GB/34GB used while
the pipeline did nothing. Hardcoding a port in every caller is what let that
drift go unnoticed, so callers should import from here instead.

HARDWARE (verified 2026-08-08)
------------------------------
- AMD Ryzen 7 9700X, 16 threads, 30GB RAM
- GPU0 ~32GB usable VRAM (Vulkan), ROCm host tooling
- Qwen3-30B-A3B-Instruct Q4_K_M resident ~20.4GB, leaving ~13GB headroom

MODEL CHOICE
------------
Qwen3-30B-A3B is Mixture-of-Experts: ~30B total parameters but only ~3B active
per token. That is why it is simultaneously the best-quality and one of the
fastest options that fits this card -- measured 95-167 tok/s warm. A dense 30B
would be several times slower for the same VRAM. Use `AGENT` for real work;
`FAST` (Mistral-7B) only for trivial high-volume classification where quality
genuinely does not matter.

PRIVACY (Stewardship P2, PRIVACY-INVARIANTS)
--------------------------------------------
Everything here stays on the box. Individual user data must never go to a hosted
model; routing it through this module is the compliant path. Do not add a cloud
fallback to these helpers -- a silent failover would turn a local-only guarantee
into a network call nobody reviewed.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

# llama-swap: OpenAI-compatible, routes by model id, one model resident at a time.
CHAT_BASE = os.environ.get("DAANAA_LLM_BASE", "http://127.0.0.1:8080/v1")
# Ollama still serves embeddings; mxbai-embed-large is the project standard (1024-dim).
EMBED_BASE = os.environ.get("DAANAA_EMBED_BASE", "http://127.0.0.1:11434")

# llama-swap slot names (see /home/akbar/warehouse/config.yaml)
ANALYSIS = "analysis"
AGENT = "agent"
CODE = "code"
FAST = "fast"

EMBED_MODEL = os.environ.get("DAANAA_EMBED_MODEL", "mxbai-embed-large")
EMBED_DIM = 1024

DEFAULT_TIMEOUT = 300  # first call may load a 17GB model from disk (~25s cold)


class LocalLLMError(RuntimeError):
    """Local inference failed. Deliberately not caught-and-cloud-fallback'd."""


def _post(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LocalLLMError(f"{url} -> HTTP {e.code}: {e.read()[:200]!r}") from e
    except Exception as e:  # connection refused, timeout, ...
        raise LocalLLMError(f"{url} unreachable: {e}") from e


def chat(
    prompt: str,
    *,
    model: str = AGENT,
    system: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """One-shot completion against the local model. Returns the text."""
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    data = _post(
        f"{CHAT_BASE}/chat/completions",
        {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout,
    )
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise LocalLLMError(f"unexpected response shape: {str(data)[:200]}") from e


def embed(text: str, *, model: str = EMBED_MODEL, timeout: int = 120) -> list[float]:
    """Embed one string. Returns a 1024-dim vector for mxbai-embed-large."""
    data = _post(
        f"{EMBED_BASE}/api/embeddings", {"model": model, "prompt": text}, timeout
    )
    vec = data.get("embedding")
    if not vec:
        raise LocalLLMError(f"no embedding in response: {str(data)[:200]}")
    return vec


def health() -> dict:
    """Report which local services are reachable. Never raises."""
    out: dict[str, object] = {}
    try:
        req = urllib.request.Request(f"{CHAT_BASE}/models")
        with urllib.request.urlopen(req, timeout=10) as r:
            out["chat"] = [m["id"] for m in json.loads(r.read()).get("data", [])]
    except Exception as e:
        out["chat"] = f"unreachable: {e}"
    try:
        req = urllib.request.Request(f"{EMBED_BASE}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as r:
            out["embed"] = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception as e:
        out["embed"] = f"unreachable: {e}"
    return out


if __name__ == "__main__":
    import pprint

    pprint.pp(health())
    print("chat:", chat("Reply with exactly: OK", max_tokens=8))
    v = embed("test")
    print(f"embed: {len(v)} dims")
