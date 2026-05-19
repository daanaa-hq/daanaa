#!/usr/bin/env python3
"""
MERIT Agent Orchestrator
------------------------
Runs the data-quality agent team nightly. Each agent decides whether it
has work to do — the orchestrator just calls them in the right order.

Schedule (managed by cron, see bottom of file):
  02:00  quality    — daily health check + report
  02:05  link_health — weekly website + donate-URL verification
  04:00  cause_tags  — tag any untagged orgs (local GPU, free)
  06:00  enrichment  — refresh stale ProPublica data (monthly cadence)

Usage:
  python3 scripts/run_agents.py                    # run all (auto-skip if current)
  python3 scripts/run_agents.py --agent link_health
  python3 scripts/run_agents.py --agent cause_tags --limit 500
  python3 scripts/run_agents.py --agent link_health --force
  python3 scripts/run_agents.py --status           # show last-run times

Cost notes:
  - link_health:  $0 (pure HTTP)
  - enrichment:   $0 (free ProPublica API)
  - cause_tags:   $0 when Ollama is up (local qwen2.5:7b)
                  ~$0.001/org if Ollama is down (Claude Haiku fallback)
  - quality:      $0 (local model summary or skipped)

  Never calls Claude Sonnet/Opus. Interactive sessions handle those tasks.
"""

import sys, argparse, logging, datetime
from pathlib import Path

# Make sure agents package is importable from anywhere
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("orchestrator")

# ── Agent registry ────────────────────────────────────────────────────────────

def load_agents():
    from agents.link_health     import LinkHealthAgent
    from agents.cause_tags      import CauseTagsAgent
    from agents.enrichment      import EnrichmentAgent
    from agents.quality         import QualityAgent
    from agents.social_presence import SocialPresenceAgent
    return {
        "quality":          QualityAgent,
        "link_health":      LinkHealthAgent,
        "cause_tags":       CauseTagsAgent,
        "enrichment":       EnrichmentAgent,
        "social_presence":  SocialPresenceAgent,
    }

# How often each agent should run (hours between runs)
CADENCE = {
    "quality":         22,      # daily
    "link_health":     6 * 24,  # weekly
    "cause_tags":      22,      # daily (skips quickly if nothing to tag)
    "enrichment":      29 * 24, # monthly
    "social_presence": 7 * 24,  # weekly
}


def show_status(agents):
    print(f"\n{'Agent':<14} {'Last run':<22} {'Due?'}")
    print("-" * 52)
    for name, cls in agents.items():
        a = cls()
        lr = a.last_run()
        hrs = a.hours_since_last_run()
        due = "YES" if hrs >= CADENCE[name] else f"in {CADENCE[name]-hrs:.0f}h"
        lr_str = lr.strftime("%Y-%m-%d %H:%M UTC") if lr else "never"
        print(f"  {name:<12} {lr_str:<22} {due}")
    print()


def run_all(agents, force=False, limit=None):
    results = {}
    for name, cls in agents.items():
        agent = cls()
        hrs   = agent.hours_since_last_run()
        if not force and hrs < CADENCE[name]:
            log.info(f"Skipping {name} — ran {hrs:.1f}h ago (cadence={CADENCE[name]}h)")
            continue
        log.info(f"Running {name}")
        kwargs = {}
        if limit and name in ("cause_tags", "link_health", "enrichment"):
            kwargs["limit"] = limit
        if force:
            kwargs["force"] = True
        try:
            results[name] = agent.run(**kwargs)
        except Exception as e:
            log.error(f"{name} failed: {e}")
            results[name] = {"error": str(e)}
    return results


def run_one(agents, name, force=False, limit=None):
    if name not in agents:
        log.error(f"Unknown agent '{name}'. Available: {list(agents)}")
        sys.exit(1)
    agent = agents[name]()
    kwargs = {}
    if limit:
        kwargs["limit"] = limit
    if force:
        kwargs["force"] = True
    return agent.run(**kwargs)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="MERIT agent orchestrator")
    ap.add_argument("--agent",  help="Run a specific agent by name")
    ap.add_argument("--force",  action="store_true", help="Ignore cadence, run anyway")
    ap.add_argument("--limit",  type=int, help="Limit rows processed (for testing)")
    ap.add_argument("--status", action="store_true", help="Show last-run times and exit")
    args = ap.parse_args()

    agents = load_agents()

    if args.status:
        show_status(agents)
        return

    log.info(f"MERIT agent run started — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    if args.agent:
        run_one(agents, args.agent, force=args.force, limit=args.limit)
    else:
        run_all(agents, force=args.force, limit=args.limit)

    log.info("All done")


if __name__ == "__main__":
    main()


# ── Cron setup ────────────────────────────────────────────────────────────────
# Add these lines to crontab (run: crontab -e):
#
#   VENV=/home/akbar/meritgiving/venv/bin/python3
#   SCRIPT=/home/akbar/meritgiving/scripts/run_agents.py
#   LOGDIR=/home/akbar/meritgiving/logs
#
#   # Daily: quality check + cause tags
#   0 2 * * * $VENV $SCRIPT --agent quality     >> $LOGDIR/agent_quality.log 2>&1
#   5 2 * * * $VENV $SCRIPT --agent cause_tags  >> $LOGDIR/agent_cause_tags.log 2>&1
#
#   # Weekly: link health (Sundays 4am)
#   0 4 * * 0 $VENV $SCRIPT --agent link_health >> $LOGDIR/agent_link_health.log 2>&1
#
#   # Monthly: ProPublica enrichment (1st of month, 6am)
#   0 6 1 * * $VENV $SCRIPT --agent enrichment  >> $LOGDIR/agent_enrichment.log 2>&1
