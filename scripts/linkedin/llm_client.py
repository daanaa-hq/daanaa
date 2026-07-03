"""
Shared LLM client for Daanaa marketing scripts.

Routes to the local Vulkan GPU server (port 11437, Qwen3-30B-A3B MoE)
which is 2-3x faster than Ollama CPU and a larger model.

Fallback: Ollama on port 11434 if 11437 is down.
"""
import json
import urllib.request
import urllib.error

GPU_URL  = "http://localhost:11437/v1/chat/completions"
FALLBACK = "http://localhost:11434/api/generate"
MODEL    = "Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf"
FALLBACK_MODEL = "qwen2.5:7b"

_gpu_available: bool | None = None   # cached after first check


def _check_gpu() -> bool:
    global _gpu_available
    if _gpu_available is not None:
        return _gpu_available
    try:
        urllib.request.urlopen("http://localhost:11437/health", timeout=2)
        _gpu_available = True
    except Exception:
        _gpu_available = False
    return _gpu_available


def generate(prompt: str, max_tokens: int = 1024, temperature: float = 0.75) -> str:
    """Generate text. Uses GPU server (11437) with Ollama fallback."""
    if _check_gpu():
        payload = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            GPU_URL, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"  GPU server error ({e}), falling back to Ollama...")

    # Ollama fallback
    payload = json.dumps({
        "model": FALLBACK_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }).encode()
    req = urllib.request.Request(
        FALLBACK, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())["response"].strip()


def generate_batch(prompts: list[str], max_tokens: int = 1024,
                   temperature: float = 0.75, workers: int = 4) -> list[str]:
    """Generate multiple prompts in parallel using CPU thread pool (each call hits GPU serially,
    but overlap helps when GPU is fast and there's Python overhead between calls)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = [""] * len(prompts)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(generate, p, max_tokens, temperature): i
                   for i, p in enumerate(prompts)}
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                results[idx] = fut.result()
            except Exception as e:
                results[idx] = f"ERROR: {e}"
    return results
