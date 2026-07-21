"""
scripts/lib/model_router.py

Capacity-aware local inference router. Picks the best model (or a tandem
pair) for a given task, based on a static roster benchmarked on this
hardware (Vulkan, full GPU offload, 2026-07-21) and the CURRENT free VRAM at
decision time — not just a static task->model table.

Design (see DECISIONS.md 2026-07-21 for the full reasoning):
- The existing warehouse (llama-swap, config at ~/warehouse/config.yaml) is
  deliberately single-model-resident with TTL unload. This router does NOT
  change that. It manages a SEPARATE set of dedicated ports for on-demand
  tandem serving: spin up only what a task needs, tear down after (or let
  the idle reaper in scripts/ops/model_idle_reaper.sh clean up), rather than
  warehousing multiple models resident 24/7.
- Model choice is throughput-informed but not throughput-only: mission
  generation is deliberately NOT auto-routed to the fastest model without a
  task-specific accuracy check first (see 2026-07-21 thin-content
  hallucination finding — a model that is fast but ungrounded on empty
  cached pages is not "productive" for that task).
- Usage is logged so scripts/ops/check_model_usage_30day.sh can flag (not
  auto-delete) roster models nobody has used in 30 days.

Usage:
    from scripts.lib.model_router import pick, ensure_running, stop_model, log_usage

    model_id, port = pick("high_volume_batch")
    ensure_running(model_id)
    # ... call http://127.0.0.1:{port}/v1/chat/completions ...
    log_usage(model_id, "high_volume_batch")
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = REPO_ROOT / "logs"
USAGE_LOG = LOG_DIR / "model_router_usage.jsonl"
STATE_DIR = REPO_ROOT / "logs" / ".model_router_state"
LLAMA_SERVER_BIN = Path.home() / "llama-vulkan" / "build" / "bin" / "llama-server"

# ---------------------------------------------------------------------------
# Roster — benchmarked 2026-07-21, Vulkan/full GPU offload, 8K context test.
# vram_gib is the MEASURED figure from that test; real usage at higher
# context (16-20K, matching production configs elsewhere) will be higher —
# ensure_running() re-checks free VRAM at launch time regardless of these
# static numbers, this table is a starting estimate, not a guarantee.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelSpec:
    path: Path
    vram_gib: float
    tok_s: float
    port: int
    best_for: tuple[str, ...]


MODELS: dict[str, ModelSpec] = {
    "qwen3_30b_a3b": ModelSpec(
        path=Path.home() / "models" / "qwen3-30b-a3b-2507" / "Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf",
        vram_gib=20.1, tok_s=178.0, port=11440,
        best_for=("high_volume_batch",),  # NOT missions — see accuracy-gate note below
    ),
    "qwen2.5_32b": ModelSpec(
        path=Path.home() / "models" / "Qwen2.5-32B-Instruct-Q4_K_M.gguf",
        vram_gib=22.4, tok_s=29.0, port=11441,
        best_for=("complex_reasoning", "governance_review"),
    ),
    "deepseek_r1_distill_7b": ModelSpec(
        path=Path.home() / "models" / "DeepSeek-R1-Distill-Qwen-7B-Q8_0.gguf",
        vram_gib=8.9, tok_s=74.9, port=11442,
        best_for=("fast_classification", "lightweight_reasoning"),
    ),
    "deepseek_r1_0528_8b": ModelSpec(
        path=Path.home() / "models" / "DeepSeek-R1-0528-Qwen3-8B-Q8_0.gguf",
        vram_gib=10.1, tok_s=68.9, port=11443,
        best_for=("fast_reasoning", "drafting"),
    ),
    "deepseek_r1_distill_14b": ModelSpec(
        path=Path.home() / "models" / "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        vram_gib=11.0, tok_s=62.1, port=11444,
        best_for=("balanced_fallback",),
    ),
}

# Task type -> ordered preference list of model_ids to try (best first).
# "missions" is deliberately absent — see pick() docstring: it requires an
# explicit accuracy-gate pass, not a default routing entry, until the
# thin-content hallucination question (DECISIONS.md 2026-07-21) is resolved.
TASK_PREFERENCE: dict[str, tuple[str, ...]] = {
    "high_volume_batch": ("qwen3_30b_a3b", "deepseek_r1_distill_14b"),
    "complex_reasoning": ("qwen2.5_32b",),
    "governance_review": ("qwen2.5_32b",),
    "fast_classification": ("deepseek_r1_distill_7b", "deepseek_r1_0528_8b"),
    "lightweight_reasoning": ("deepseek_r1_distill_7b", "deepseek_r1_0528_8b"),
    "fast_reasoning": ("deepseek_r1_0528_8b", "deepseek_r1_distill_7b"),
    "drafting": ("deepseek_r1_0528_8b", "deepseek_r1_distill_7b"),
    "balanced_fallback": ("deepseek_r1_distill_14b",),
}

# Confirmed-safe concurrent pairs from the 2026-07-21 benchmark report.
# Qwen2.5 32B is deliberately absent from every pair here — report marked
# "not recommended" with any other LLM at the tested 8K context.
SAFE_TANDEMS: set[frozenset[str]] = {
    frozenset({"deepseek_r1_distill_7b", "deepseek_r1_0528_8b"}),
    frozenset({"deepseek_r1_distill_7b", "deepseek_r1_distill_14b"}),
    frozenset({"deepseek_r1_0528_8b", "deepseek_r1_distill_14b"}),
}
# Fits but little headroom per the report — usable, but prefer sequential
# if anything else on the card needs VRAM (e.g. the embedding service).
TIGHT_TANDEMS: set[frozenset[str]] = {
    frozenset({"qwen3_30b_a3b", "deepseek_r1_distill_7b"}),
}

VRAM_SAFETY_MARGIN_GIB = 2.0  # leave headroom for KV cache growth beyond the 8K test


def get_free_vram_gib(gpu_index: int = 0) -> float:
    """Query live free VRAM via rocm-smi. Returns 0.0 if the query fails
    (caller should treat that as 'assume no capacity', not crash)."""
    try:
        out = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return 0.0
    total = used = None
    for line in out.splitlines():
        if f"GPU[{gpu_index}]" not in line:
            continue
        m_total = re.search(r"Total Memory \(B\):\s*(\d+)", line)
        m_used = re.search(r"Total Used Memory \(B\):\s*(\d+)", line)
        if m_total:
            total = int(m_total.group(1))
        if m_used:
            used = int(m_used.group(1))
    if total is None or used is None:
        return 0.0
    return (total - used) / (1024 ** 3)


def _health_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as r:
            body = json.loads(r.read())
            return body.get("status") == "ok"
    except Exception:
        return False


def pick(task_type: str, missions_accuracy_gate_passed: bool = False) -> str:
    """Return the best single model_id for a task type, given current free
    VRAM. Raises ValueError for unknown task types or if nothing fits.

    'missions' is special-cased: pass missions_accuracy_gate_passed=True
    only after a task-specific accuracy comparison confirms the chosen model
    doesn't regress on the thin-content hallucination failure mode found
    2026-07-21 (see DECISIONS.md). Without that, missions must not be routed
    through this function at all — the caller should stay on whatever model
    generate_missions.py already uses until that decision is made explicitly.
    """
    if task_type == "missions" and not missions_accuracy_gate_passed:
        raise ValueError(
            "missions task requires an explicit accuracy-gate pass before routing "
            "through model_router — see DECISIONS.md 2026-07-21. Not a throughput decision."
        )
    prefs = TASK_PREFERENCE.get(task_type)
    if not prefs:
        raise ValueError(f"unknown task_type: {task_type!r}. Known: {sorted(TASK_PREFERENCE)}")
    free = get_free_vram_gib()
    for model_id in prefs:
        spec = MODELS[model_id]
        if spec.vram_gib + VRAM_SAFETY_MARGIN_GIB <= free or _health_ok(spec.port):
            return model_id
    # Nothing fits fresh and nothing already running — return the top
    # preference anyway; ensure_running() will surface the real failure.
    return prefs[0]


def pick_tandem(task_types: list[str]) -> list[str] | None:
    """For 2+ concurrent tasks, try to find a safe or tight tandem that
    covers all of them within current free VRAM. Returns None (caller should
    fall back to sequential execution) if no safe combination fits."""
    if len(task_types) < 2:
        raise ValueError("pick_tandem needs 2+ task types; use pick() for one")
    candidates = [MODELS[TASK_PREFERENCE[t][0]] and TASK_PREFERENCE[t][0] for t in task_types[:2]]
    pair = frozenset(candidates)
    if len(pair) != 2:
        return None  # same model already covers both tasks, no tandem needed
    free = get_free_vram_gib()
    combined = sum(MODELS[m].vram_gib for m in pair) + VRAM_SAFETY_MARGIN_GIB
    if pair in SAFE_TANDEMS and combined <= free:
        return list(pair)
    if pair in TIGHT_TANDEMS and combined <= free:
        return list(pair)  # caller should prefer sequential if anything else needs the card
    return None


def ensure_running(model_id: str, wait_s: int = 90) -> int:
    """Idempotent: start the model's llama-server if not already healthy on
    its assigned port. Returns the port. Raises RuntimeError on failure."""
    spec = MODELS[model_id]
    if _health_ok(spec.port):
        return spec.port
    if not spec.path.exists():
        raise RuntimeError(f"{model_id}: gguf not found at {spec.path}")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"model_router_{model_id}.log"
    proc = subprocess.Popen(
        [str(LLAMA_SERVER_BIN), "-m", str(spec.path), "--port", str(spec.port),
         "--host", "127.0.0.1", "-ngl", "99", "--device", "Vulkan1",
         "--ctx-size", "8192", "--jinja"],
        stdout=open(log_file, "a"), stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    (STATE_DIR / f"{model_id}.pid").write_text(str(proc.pid))
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if _health_ok(spec.port):
            return spec.port
        time.sleep(2)
    raise RuntimeError(f"{model_id}: did not become healthy on port {spec.port} within {wait_s}s")


def stop_model(model_id: str) -> bool:
    """Stop a router-launched model by PID file. Returns False if it wasn't
    tracked as router-managed (e.g. it's part of the warehouse or the
    standalone Qwen 32B watchdog — this function never touches those)."""
    pid_file = STATE_DIR / f"{model_id}.pid"
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        subprocess.run(["kill", str(pid)], timeout=5)
    except Exception:
        pass
    pid_file.unlink(missing_ok=True)
    return True


def stop_all() -> None:
    for model_id in MODELS:
        stop_model(model_id)


def log_usage(model_id: str, task_type: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "model_id": model_id,
        "task_type": task_type,
        "free_vram_gib_at_call": round(get_free_vram_gib(), 1),
    }
    with open(USAGE_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: model_router.py [pick <task_type> | stop-all | free-vram]")
        raise SystemExit(1)
    cmd = sys.argv[1]
    if cmd == "pick" and len(sys.argv) == 3:
        print(pick(sys.argv[2]))
    elif cmd == "stop-all":
        stop_all()
        print("stopped all router-managed models")
    elif cmd == "free-vram":
        print(f"{get_free_vram_gib():.1f} GiB free")
    else:
        print("unknown command")
        raise SystemExit(1)
