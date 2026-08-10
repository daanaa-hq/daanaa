# Daemon Health Standard

**Adopted:** 2026-08-10, after two independent bugs in the same session both
let a broken pipeline report itself healthy for ~15.4 days.

## The rule

**Any long-running process publishes its own state. Its watchdog/monitor reads
that state and applies a pure decision function. Neither ever infers health
from log text (grep, line-counting, symbol-counting).**

That's the whole standard. Everything below is why, and how to apply it in
~20 minutes to a new daemon.

## Why this exists

Two bugs, same session, same root cause class:

1. **`watchdog_discovery.sh`** grepped log text for `"abandoning 50 stuck"`
   — a batch-size literal. The daemon's actual batch size changed to 100.
   The grep silently stopped matching anything, and a proven kill-and-restart
   fix (built live, twice, in the 2026-07-20/21 incident) sat dead for
   ~15.4 days while the watchdog logged "still producing — watching, not
   restarting yet" every 5 minutes.

2. **`monitor_discovery_health.py`** counted `✅`/`⚪` symbols in the last
   1000 log lines as a "discovered" proxy, and its alert condition was
   `success_rate < THRESHOLD and discovered > 0` — the `discovered > 0`
   guard existed to avoid a division-by-zero at startup, but its side effect
   was that `discovered == 0` (the daemon alive and producing *nothing*)
   silently skipped the alert. It reported "✅ Daemon healthy" every hour for
   370 consecutive checks while producing zero output the entire time.

Neither bug required a crash, an exception, or a process dying. Both were a
monitoring layer confidently reporting green while the thing it watched was
red — the specific failure mode Toyota's Jidoka principle exists to prevent
(a machine should stop itself and signal the instant it detects its own
defect, not require a human to notice a contradiction between two logs).

See `governance/LESSONS.md` (2026-08-10 entries) for the full incident
writeups.

## The pattern

```
┌─────────────┐   writes state    ┌──────────────────┐   reads state    ┌────────────┐
│   Daemon     │ ────atomically──▶│  state.json       │ ◀────────────────│  Watchdog  │
│ (does work)  │   every iteration │ (pid, counters,   │                  │ (decides)  │
└─────────────┘                    │  last_updated_at) │                  └────────────┘
                                    └──────────────────┘
```

1. **The daemon writes its own state**, atomically (`tmp` file + `rename`,
   never a partial write a reader could see), after every unit of work
   (batch, iteration, request cycle — whatever "one tick" means for that
   process). Minimum required fields:
   - `pid` — so a stale snapshot from a prior process is detectable
   - `last_updated_at` — ISO timestamp, so staleness is detectable
   - at least one **monotonic** counter for real output (not "attempts",
     actual successes) — this is what a stuck-but-alive process can't fake
   - any counters needed for a stuck-pattern check specific to that daemon

2. **A pure decision function** (`scripts/daemon_health_lib.py`) takes the
   state, a liveness bool, and the current pid, and returns one of:
   `restart` / `ok` / `unknown_no_state` / `unknown_stale_pid`. It never does
   file or process I/O itself — that separation is what makes it trivially
   unit-testable with synthetic states, including the exact incident states
   above (see `tests/test_daemon_health_lib.py`).

3. **`unknown_*` is not `ok`.** The single most important property this
   standard buys you: if there's no trustworthy signal yet, the function
   says so explicitly, so the caller can fall back to something else (or
   wait) instead of the absence of information quietly defaulting to
   "healthy" — which is exactly how both bugs above went unnoticed.

4. **The watchdog/monitor is a thin shell wrapper** that gathers the two
   real-world facts (is the pid alive, read the state file) and calls the
   decision function — via a small Python CLI if the watchdog itself is
   bash. Decision logic lives in one Python file, testable in isolation;
   bash only does process management (kill, restart, cron).

## How to apply this to a new daemon (~20 min)

1. Add a `_write_state_snapshot()` method to the daemon, called once per
   work cycle. Copy the atomic-write pattern from
   `scripts/daemon_health_lib.py:write_state_atomic()` or
   `scripts/discovery_daemon.py:_write_state_snapshot()`.
2. Decide what "stuck" means for this daemon (if anything — a simple
   HTTP-health-check daemon may only need liveness + staleness, no stuck
   pattern at all; pass `stuck_thresholds=None`).
3. Write a 10-20 line wrapper module (see `discovery_daemon_health.py`) that
   calls `daemon_health_lib.evaluate_health()` with this daemon's specific
   thresholds and state-file path.
4. Write tests against synthetic state dicts — no real process needed. Copy
   `tests/test_discovery_daemon_health.py`'s structure.
5. Point the watchdog/cron at the wrapper's CLI instead of grepping logs.

## What this standard does NOT require

- It does not require rewriting a daemon's actual work logic.
- It does not require a database, a message queue, or any new service — the
  state file is a local JSON file, same trust model as an ordinary log.
- It does not require every daemon to have identical fields — only the
  minimum four (`pid`, `last_updated_at`, one monotonic output counter,
  whatever stuck-detection fields that specific daemon needs).

## Current status across this codebase

| Daemon/watchdog | Status |
|---|---|
| `discovery_daemon.py` + `watchdog_discovery.sh` | ✅ Migrated 2026-08-10, proven live (real restart fired, real recovery confirmed) |
| `monitor_discovery_health.py` | ✅ Zero-output blind spot fixed 2026-08-10, now cross-checks daemon state |
| `watchdog_llama.sh` | ⚠️ Not yet audited against this standard. Currently does a real HTTP `/health` check (better than pure liveness) but has no throughput/stuck-pattern detection — could return `200` while hung mid-inference. Candidate for the next pass. |
| `agent7_daemon.py`, `daemon_monitor.py`, `monitor_daemon_memory.py` | ⚠️ Not yet audited. Unknown whether they share either bug class above. |

Audit the remaining three before assuming they're fine — this standard
exists because "it's probably fine" was the operating assumption for 15
days on the one we did check.
