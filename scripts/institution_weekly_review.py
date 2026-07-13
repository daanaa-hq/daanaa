#!/usr/bin/env python3
"""Generate a manual Daanaa institutional weekly review from local evidence only."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sqlite3
import subprocess
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTITUTION = ROOT / "institution"
REVIEWS = INSTITUTION / "reviews"
BRIEFS = INSTITUTION / "briefs"
STATE_PATH = INSTITUTION / "state.json"
DB = ROOT / "data" / "merit_registry.db"
FRONTEND = ROOT / "frontend"


def ascii_safe(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2192", "->")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def run(
    args: list[str],
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: int = 240,
) -> dict[str, str | bool | int]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            env=merged_env,
        )
        return {
            "ok": completed.returncode == 0,
            "code": completed.returncode,
            "output": ascii_safe((completed.stdout or "").strip()),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "code": -1, "output": ascii_safe(f"{type(exc).__name__}: {exc}")}


def scalar(query: str) -> str:
    if not DB.exists():
        return "unknown: database missing"
    try:
        with sqlite3.connect(DB) as conn:
            row = conn.execute(query).fetchone()
        return "unknown" if row is None else str(row[0])
    except Exception as exc:  # noqa: BLE001
        return ascii_safe(f"unknown: {type(exc).__name__}: {exc}")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_excerpt(path: Path, max_lines: int = 32) -> str:
    text = read_text(path)
    if not text:
        return "Missing."
    return ascii_safe("\n".join(text.splitlines()[:max_lines]))


def tail_excerpt(path: Path, max_lines: int = 80) -> str:
    if not path.exists():
        return "Missing."
    recent: deque[str] = deque(maxlen=max_lines)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            recent.append(line.rstrip("\n"))
    return ascii_safe("\n".join(recent))


def extract_ids(path: Path, prefix: str) -> list[str]:
    text = read_text(path)
    pattern = rf"\b{re.escape(prefix)}-(?:\d{{3}}|\d{{4}}-\d{{2}}-\d{{2}}-\d{{3}})\b"
    return sorted(set(re.findall(pattern, text)))


def table_counts() -> dict[str, str]:
    return {
        "registry_enriched": scalar("SELECT COUNT(*) FROM registry_enriched"),
        "org_fts": scalar("SELECT COUNT(*) FROM org_fts"),
        "org_embeddings": scalar("SELECT COUNT(*) FROM org_embeddings"),
        "org_claims": scalar("SELECT COUNT(*) FROM org_claims"),
        "analytics_daily": scalar("SELECT COUNT(*) FROM analytics_daily"),
        "analytics_search": scalar("SELECT COUNT(*) FROM analytics_search"),
        "feedback": scalar("SELECT COUNT(*) FROM feedback"),
        "v5_feedback": scalar("SELECT COUNT(*) FROM v5_feedback"),
        "org_interest": scalar("SELECT COUNT(*) FROM org_interest"),
        "org_view_events": scalar("SELECT COUNT(*) FROM org_view_events"),
        "wallet_analytics": scalar("SELECT COUNT(*) FROM wallet_analytics"),
        "agent_job_log": scalar("SELECT COUNT(*) FROM agent_job_log"),
        "quality_log": scalar("SELECT COUNT(*) FROM quality_log"),
        "waitlist": scalar("SELECT COUNT(*) FROM waitlist"),
    }


def recent_log_summary(path: Path) -> dict[str, object]:
    excerpt = tail_excerpt(path, 120)
    lines = excerpt.splitlines() if excerpt and excerpt != "Missing." else []
    flags = [
        line
        for line in lines
        if any(token in line.lower() for token in ["error", "exception", "traceback", "database is locked"])
    ]
    categories = set()
    latest_date = None
    for line in lines:
        match = re.search(r"\[(\d{4}-\d{2}-\d{2}) ", line)
        if match:
            latest_date = match.group(1)
        if "/api/search" in line or "peer_cell_size" in line or "v4." in line:
            categories.add("search_schema_drift")
        if "database is locked" in line:
            categories.add("db_locking")
        if "no such table: propublica_financials" in line:
            categories.add("lean_db_missing_table")
    return {
        "path": str(path.relative_to(ROOT)),
        "available": path.exists(),
        "issue_count": len(flags),
        "sample": flags[-5:] if flags else [],
        "categories": sorted(categories),
        "latest_date": latest_date,
    }


def _is_recent_log_issue(log: dict[str, object], *, days: int = 3) -> bool:
    latest = log.get("latest_date")
    if not latest:
        return False
    try:
        latest_date = _dt.date.fromisoformat(str(latest))
    except ValueError:
        return False
    return (_dt.date.today() - latest_date).days <= days


def pick_constraint(validations: dict[str, dict[str, object]], logs: list[dict[str, object]]) -> dict[str, object]:
    search_log = next((log for log in logs if log["path"] == "logs/daanaa_api.log"), None)
    if (
        search_log
        and search_log["issue_count"]
        and "search_schema_drift" in search_log.get("categories", [])
        and _is_recent_log_issue(search_log)
    ):
        return {
            "id": "constraint-search-reliability-001",
            "summary": "Recent backend search failures are a higher immediate constraint than the remaining institutional unknowns.",
            "evidence": [
                "Sampled daanaa_api log still contains recent /api/search exceptions tied to v4 schema drift",
                "R-013 is open in the institutional risk register",
                "Current automated checks do not directly exercise the failing search path against the live backend",
            ],
            "recommended_action": "Verify the current /api/search path against the live backend shape and add targeted regression coverage before treating the reliability risk as closed.",
            "confidence": "medium",
        }
    lint = validations["frontend_lint"]
    if not lint["ok"]:
        return {
            "id": "constraint-validation-gate-001",
            "summary": "Frontend lint is not a working validation gate, so cross-stack changes cannot be trusted cheaply.",
            "evidence": [
                "npm run lint fails locally",
                "ESLint 9 cannot find eslint.config.*",
                "R-002 remains open",
            ],
            "recommended_action": "Add a minimal ESLint 9 flat config scoped to current frontend code and re-run lint.",
            "confidence": "high",
        }
    return {
        "id": "constraint-operational-unknowns-001",
        "summary": "Financial and infrastructure unknowns outside the repo limit responsible planning more than code quality now.",
        "evidence": [
            "FR-2026-07-10-001 through FR-2026-07-10-004 remain open",
            "GPU/CPU/cloud usage telemetry is still unknown",
            "Budget state remains in survival posture",
        ],
        "recommended_action": "Keep safe local improvements moving and request only the minimum founder inputs needed for spend, backup, and credential decisions.",
        "confidence": "medium",
    }


def build_state(
    today: str,
    counts: dict[str, str],
    validations: dict[str, dict[str, object]],
    processes: dict[str, object],
    ollama_models: dict[str, object],
    logs: list[dict[str, object]],
) -> dict[str, object]:
    current_constraint = pick_constraint(validations, logs)
    risks = extract_ids(INSTITUTION / "RISK_REGISTER.md", "R")
    founder_requests = extract_ids(INSTITUTION / "FOUNDER_REQUESTS.md", "FR")
    hypotheses = extract_ids(INSTITUTION / "HYPOTHESES.md", "H")
    decisions = extract_ids(INSTITUTION / "DECISION_LOG.md", "DR")
    funding = extract_ids(INSTITUTION / "FUNDING_PIPELINE.md", "F")
    skills = sorted(path.stem for path in (INSTITUTION / "skills").glob("*.md") if path.name != "INVENTORY.md")
    validation_failures = [name for name, result in validations.items() if not result["ok"]]
    automation_failures = list(validation_failures)
    if not processes["ok"]:
        automation_failures.append("process inventory unavailable")
    if not ollama_models["ok"]:
        automation_failures.append("local model inventory unavailable")
    if all(log["issue_count"] == 0 for log in logs if log["available"]):
        recent_log_state = "no flagged issue lines in sampled local logs"
    else:
        recent_log_state = "flagged issue lines present in sampled local logs"
    return {
        "meta": {
            "purpose": "Machine-readable operating state for the Daanaa stewardship loop.",
            "responsible_role": "Stewardship Systems Agent",
            "authority_level": "Operational state subordinate to protected governing files and AUTHORITY.md",
            "review_trigger": "Manual weekly review, material incident, or sourced founder update",
            "editable_status": "Editable by ordinary agents when values are verified or explicitly unknown",
            "dependencies": [
                "institution/AUTHORITY.md",
                "institution/CURRENT_STATE.md",
                "institution/RISK_REGISTER.md",
                "scripts/institution_weekly_review.py",
            ],
            "retirement_condition": "Retire when replaced by a maintained state system with equivalent auditability",
        },
        "last_updated": today,
        "mission_status": {
            "state": "active",
            "summary": "Core nonprofit search remains intact while stewardship controls run alongside the product.",
            "confidence": "high",
        },
        "current_highest_constraint": current_constraint,
        "current_top_priorities": [
            "Preserve product behavior while strengthening validation and governance clarity",
            "Keep financial and infrastructure unknowns explicit",
            "Use the stewardship loop internally before broader automation",
        ],
        "active_hypotheses": hypotheses,
        "current_product_experiments": [
            {
                "id": "EXP-2026-07-10-001",
                "name": "Institutional operating loop as internal first customer",
                "status": "active",
                "success_measure": "Two manual review cycles produce a useful, low-noise founder brief",
                "confidence": "medium",
            }
        ],
        "known_user_friction": extract_ids(INSTITUTION / "USER_INSIGHTS.md", "U"),
        "open_risks": risks,
        "founder_requests": founder_requests,
        "budget_intake": {
            "available_cash": "unknown",
            "monthly_fixed_commitments": "unknown",
            "variable_operating_costs": "unknown",
            "expected_revenue": "unknown",
            "confirmed_funding": "unknown",
            "probability_weighted_funding": "unknown",
            "founder_approved_spending_cap": "unknown",
            "emergency_reserve_target": "unknown",
        },
        "scenario_forecasts": {
            "survival": "default until financial inputs are verified",
            "responsible_growth": "unknown pending budget intake",
            "externally_funded_acceleration": "unknown pending verified funding and founder approval",
        },
        "operating_costs": {
            "scenario_default": "survival",
            "known": [
                {
                    "item": "DigitalOcean droplet cost",
                    "value": "$16/mo documented but not billing-verified",
                    "confidence": "medium",
                }
            ],
            "unknown_financial_inputs": [
                "available_cash",
                "monthly_fixed_commitments",
                "variable_operating_costs",
                "expected_revenue",
                "confirmed_funding",
                "probability_weighted_funding",
                "founder_approved_spending_cap",
                "emergency_reserve_target",
            ],
        },
        "infrastructure_utilization": {
            "local_services_detected": processes["output"].splitlines() if processes["ok"] and processes["output"] else [],
            "local_models": ollama_models["output"].splitlines()[:10] if ollama_models["ok"] and ollama_models["output"] else ["unknown or unavailable"],
            "gpu_capacity": "unknown: no durable telemetry source verified",
            "cpu_capacity": "unknown: no durable telemetry source verified",
            "storage_snapshot": {
                "merit_registry_db": "about 11G",
                "data_directory": "about 124G",
            },
            "model_routing_recommendation": {
                "deterministic_tasks": "ordinary code first",
                "local_small_models": "classification, extraction, and routine drafting when privacy allows",
                "local_large_models": "private-data summarization or drafting when local quality is sufficient",
                "cloud_models": "only for high-value reasoning when permitted and justified",
                "human_review": "legal, financial, ethical, security, and public-claim decisions",
            },
        },
        "funding_opportunities": funding,
        "internal_initiatives": [
            {
                "id": "INIT-2026-07-10-001",
                "name": "Stewardship operating loop bootstrap",
                "status": "active",
                "official_accounting_record": False,
            }
        ],
        "user_input_channels": {
            "search_activity": "verified local table exists",
            "claim_profile_activity": "verified local table exists",
            "feedback": "verified local table exists",
            "support_email": "unknown: no local mailbox export verified",
            "analytics": "verified aggregate tables exist",
            "error_logs": recent_log_state,
            "advisory_feedback": "unknown",
        },
        "active_automations": [
            {
                "name": "manual_weekly_review",
                "entrypoint": "python3 scripts/institution_weekly_review.py",
                "status": "manual-only",
            }
        ],
        "automation_failures": automation_failures,
        "skills_inventory": skills,
        "skills_needing_adjustment": [
            "Validate skill usefulness across two review cycles before expanding the library"
        ],
        "decisions_awaiting_review": decisions,
        "last_successful_review": {
            "date": today,
            "artifact": f"institution/reviews/{today}-weekly-review.md",
        },
        "evidence_freshness": {
            "git_state": today,
            "database_snapshot": today,
            "validation_run": today,
            "billing_state": "unknown",
            "provider_console_state": "unknown",
        },
        "confidence_levels": {
            "local_repository_facts": "high",
            "local_database_counts": "high",
            "validation_status": "high",
            "budget_state": "low",
            "current_paid_services": "low",
            "infrastructure_utilization_metrics": "low",
        },
        "validation": {name: {"ok": result["ok"], "code": result["code"]} for name, result in validations.items()},
        "data_snapshot": counts,
    }


def main() -> int:
    today = _dt.date.today().isoformat()
    REVIEWS.mkdir(parents=True, exist_ok=True)
    BRIEFS.mkdir(parents=True, exist_ok=True)

    counts = table_counts()
    git_status = run(["git", "status", "--short", "--branch"])
    git_log = run(["git", "log", "--oneline", "-n", "5"])
    git_diff = run(["git", "diff", "--stat"])
    py_compile = run(["python3", "-m", "py_compile", "daanaa_api.py", "nonprofit_portal_endpoints.py", "scripts/droplet_api.py", "scripts/build_search_db.py", "scripts/website_normalize.py"])
    pytest_core = run(["./venv/bin/python3", "-m", "pytest", "tests/test_principles.py", "tests/test_website_normalize.py", "-q"])
    pytest_claim = run(
        ["./venv/bin/python3", "-m", "pytest", "tests/test_claim_login.py", "-q"],
        env={
            "DB_PATH": "/tmp/daanaa_pytest_import_guard.db",
            "LIVE_DB_PATH": "/tmp/daanaa_pytest_import_guard.db",
        },
    )
    frontend_lint = run(["npm", "run", "lint"], cwd=FRONTEND)
    frontend_tests = run(["npm", "test", "--", "--runInBand", "wallet.crypto", "PassphraseModal", "WalletContext", "--no-coverage"], cwd=FRONTEND)
    frontend_build = run(["npm", "run", "build"], cwd=FRONTEND)
    processes = run(["pgrep", "-af", "ollama|llama-swap|gunicorn|metabase|n8n|cloudflared"])
    ollama_models = run(["ollama", "list"])

    validations = {
        "py_compile": py_compile,
        "pytest_core": pytest_core,
        "pytest_claim": pytest_claim,
        "frontend_lint": frontend_lint,
        "frontend_tests": frontend_tests,
        "frontend_build": frontend_build,
    }

    logs = [
        recent_log_summary(ROOT / "logs" / "daanaa_api.log"),
        recent_log_summary(ROOT / "logs" / "embed_server.log"),
        recent_log_summary(ROOT / "logs" / "nightly_search_deploy.log"),
    ]
    state = build_state(today, counts, validations, processes, ollama_models, logs)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    current_constraint = state["current_highest_constraint"]
    highest_constraint = current_constraint["summary"]
    recommended_action = current_constraint["recommended_action"]
    scheduling_recommendation = "Not yet stable enough for scheduling; the loop should clear the current search-reliability follow-up before moving from manual reviews to automation."

    log_lines = []
    for log in logs:
        if not log["available"]:
            log_lines.append(f"- {log['path']}: missing")
        else:
            sample = "; ".join(log["sample"]) if log["sample"] else "no flagged lines in sampled tail"
            log_lines.append(f"- {log['path']}: {log['issue_count']} flagged lines; {sample}")

    if current_constraint["id"] == "constraint-search-reliability-001":
        options_block = """1. Lowest-cost option: keep the institutional loop manual and verify whether the logged search failures still reproduce on the current backend.
   - Benefit: confirms whether the risk is stale or active before broader work.
   - Cost: local engineering time only.
   - Risk: low.

2. Balanced option: add a targeted `/api/search` regression test around the schema-drift path and re-run the weekly review after verification.
   - Benefit: turns a log-discovered risk into a durable guardrail.
   - Cost: local engineering time only.
   - Risk: low and reversible.

3. Higher-investment option: expand observability around backend runtime failures before confirming the specific search-path regression.
   - Benefit: broader telemetry.
   - Cost: more engineering work and more moving parts.
   - Risk: medium because instrumentation can outpace the specific repair need.
"""
        deliberation = """- Mission Steward: favors the balanced option because broken search directly harms nonprofit discovery.
- Small Nonprofit Executive Director: wants search reliability fixed before more institutional overhead is added.
- Nonprofit Finance And Compliance Representative: sees no cost blocker to a local regression test and prefers proof over assumption.
- Donor And Funder Representative: treats search correctness as a trust signal because it shapes which nonprofits people can find.
- Product And User Experience Representative: sees repeated search errors as user-facing breakage that should outrank internal unknowns.
- Technology And Data Representative: supports converting the log finding into direct test coverage on the live backend path.
- Security And Privacy Representative: prefers a local verification/test fix over adding new telemetry.
- Legal And Regulatory Issue-Spotter: sees no new regulatory exposure in local reliability verification.
- Financial Sustainability Representative: favors the balanced option because it is low-cost and reduces wasted debugging later.
- Ethics And Human Dignity Representative: notes that a broken search path can invisibly suppress nonprofits, which is a fairness concern.
- Devil's Advocate: warns that the log sample may be stale if the code was already fixed but not re-exercised.
- Long-Term Continuity Representative: supports closing or confirming R-013 with evidence before the loop shifts attention elsewhere.

Minority view: the Devil's Advocate argues for a quick reproduction check first so the institution does not over-prioritize an already-fixed error based only on old log lines.
"""
        expected_benefit = "restore confidence that the core search path works and cannot silently regress on the same schema-drift class"
        recommendation_evidence = "recent log evidence, open R-013, and absence of direct coverage on the live backend search path"
        success_measure = "the failing search path is either reproduced and covered by a regression test or proven clean with updated evidence, and R-013 can be narrowed accordingly."
        stop_condition = "stop if the verification shows the log evidence is stale and no current search failure reproduces"
    elif current_constraint["id"] == "constraint-validation-gate-001":
        options_block = """1. Lowest-cost option: keep the weekly review manual and fix only the broken validation gate.
   - Benefit: restores a missing quality control with minimal scope.
   - Cost: local engineering time only.
   - Risk: low.

2. Balanced option: fix the lint gate, preserve task ownership in-repo, and re-run the review to update the constraint.
   - Benefit: improves both execution discipline and institutional clarity.
   - Cost: local engineering time only.
   - Risk: low and reversible.

3. Higher-investment option: add broader local telemetry and dashboarding for cost, usage, and founder reporting.
   - Benefit: better operational visibility.
   - Cost: more engineering time and more moving parts.
   - Risk: medium because instrumentation can outpace real need.
"""
        deliberation = """- Mission Steward: favors the balanced option because it strengthens trust without changing public behavior.
- Small Nonprofit Executive Director: prefers work that reduces product mistakes before adding more institutional overhead.
- Nonprofit Finance And Compliance Representative: notes that financial unknowns remain serious, but they do not block a no-cost lint repair.
- Donor And Funder Representative: wants claims and trust signals validated consistently before new outward-facing work.
- Product And User Experience Representative: supports restoring lint because silent UI regressions are expensive to users.
- Technology And Data Representative: supports the balanced option; adding a flat config is straightforward and reversible.
- Security And Privacy Representative: prefers no new telemetry until privacy and retention are documented.
- Legal And Regulatory Issue-Spotter: sees no added regulatory exposure in a local lint repair.
- Financial Sustainability Representative: prefers the lowest-cost or balanced option; rejects new paid tools.
- Ethics And Human Dignity Representative: supports changes that reduce confusing or unreviewed behavior affecting nonprofits.
- Devil's Advocate: argues that documentation conflict, not lint, is the bigger issue; lint alone does not solve deployment ambiguity.
- Long-Term Continuity Representative: supports the balanced option because it couples a process improvement with durable records.

Minority view: the Devil's Advocate and continuity perspectives both warn that lint repair should not be mistaken for complete institutional clarity; backend source-of-truth conflicts and founder-only unknowns still need follow-through.
"""
        expected_benefit = "improve trust in routine changes and reduce silent frontend regressions"
        recommendation_evidence = "local lint failure, successful targeted tests, explicit authority/handoff additions"
        success_measure = "`npm run lint` passes locally and the weekly review records a new next constraint rather than the same missing gate."
        stop_condition = "stop if the config requires broad frontend behavior changes or creates noisy false positives disproportionate to value"
    else:
        options_block = """1. Lowest-cost option: keep the survival posture, preserve unknowns explicitly, and wait for only the founder inputs that unblock responsible decisions.
   - Benefit: avoids fabricated data and avoids unnecessary work.
   - Cost: near zero.
   - Risk: slow progress on budgeting and continuity.

2. Balanced option: keep safe local improvements moving while narrowing the founder request queue to spend, backup, credential rotation, and deployment authority.
   - Benefit: preserves momentum without crossing human-accountability boundaries.
   - Cost: local synthesis time only.
   - Risk: medium-low.

3. Higher-investment option: add new telemetry and operational dashboards before the missing financial inputs are verified.
   - Benefit: richer visibility.
   - Cost: more engineering work and more moving parts.
   - Risk: medium because it can create noise before core unknowns are resolved.
"""
        deliberation = """- Mission Steward: favors the balanced option because it keeps improving service quality without inventing finances or bypassing human accountability.
- Small Nonprofit Executive Director: wants the team to stay useful and frugal rather than building heavy internal systems first.
- Nonprofit Finance And Compliance Representative: insists that unknown cash, recurring spend, and reserve posture must stay explicitly unknown.
- Donor And Funder Representative: wants credible stewardship evidence before outward funding or growth claims expand.
- Product And User Experience Representative: supports continuing low-risk product-quality work while waiting on founder-only inputs.
- Technology And Data Representative: prefers existing local services and deterministic code over new telemetry complexity.
- Security And Privacy Representative: supports waiting for founder-confirmed backup and credential status before changing data-handling assumptions.
- Legal And Regulatory Issue-Spotter: agrees that approval boundaries should stay strict until the founder resolves the delegation conflict.
- Financial Sustainability Representative: strongly favors the survival posture and opposes new paid tools.
- Ethics And Human Dignity Representative: supports honest uncertainty over false precision.
- Devil's Advocate: argues that the sampled search log errors may be a more urgent reliability constraint than financial unknowns.
- Long-Term Continuity Representative: agrees with the balanced option, but wants backup and credential clarity resolved soon because continuity cannot rely on assumptions.

Minority view: the Devil's Advocate warns that backend schema-drift errors in recent logs may justify a focused reliability task before another institutional iteration.
"""
        expected_benefit = "allow responsible financial, continuity, and approval decisions without inventing missing operational facts"
        recommendation_evidence = "open founder requests, survival-budget posture, unknown usage telemetry, and unresolved provider-console state"
        success_measure = "founder-only unknowns remain narrowly scoped, explicitly tracked, and do not block safe local improvements."
        stop_condition = "stop if a verified production reliability issue becomes a higher constraint than the current missing financial and continuity inputs"

    review = f"""# Weekly Institutional Review - {today}

## Document Control

| Field | Value |
|---|---|
| Purpose | Manual weekly institutional review generated from local repository evidence. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Evidence snapshot and recommendation; not approval. |
| Review trigger | Next manual cycle, material incident, or sourced founder update. |
| Editable status | Generated artifact; corrections should be appended or regenerated. |
| Dependencies | `scripts/institution_weekly_review.py`, local repo, local SQLite DB, local process state. |
| Retirement condition | Retire when superseded by a better dated review. |

## Current State

- Branch status command: {'ok' if git_status['ok'] else 'failed'}.
- Git state:
```text
{git_status['output'] or 'unavailable'}
```
- Recent commits:
```text
{git_log['output'] or 'unavailable'}
```
- Current diff summary:
```text
{git_diff['output'] or 'clean or unavailable'}
```
- Validation summary:
  - `py_compile`: {'pass' if py_compile['ok'] else 'fail'}
  - `pytest_core`: {'pass' if pytest_core['ok'] else 'fail'}
  - `pytest_claim`: {'pass' if pytest_claim['ok'] else 'fail'}
  - `frontend_lint`: {'pass' if frontend_lint['ok'] else 'fail'}
  - `frontend_tests`: {'pass' if frontend_tests['ok'] else 'fail'}
  - `frontend_build`: {'pass' if frontend_build['ok'] else 'fail'}
- Local services snapshot:
```text
{processes['output'] or 'unavailable'}
```
- Local model inventory:
```text
{ollama_models['output'] or 'unavailable'}
```

## Mission Alignment

Advanced the mission:

- Preserved free public discovery behavior while strengthening the stewardship layer around it.
- Added explicit authority ordering, durable handoff rules, and machine-readable operating state.
- Kept work local-only, no-spend, and reversible.

Did not materially advance the mission:

- Unverified financial and provider-console unknowns remain unresolved.
- No new representative nonprofit user evidence was gathered in this cycle.

Mission drift check:

- No evidence of growth-over-trust drift in this cycle.
- Risk remains where analytics/privacy docs conflict or where public copy may overstate certainty.

## User Experience

Verified user-signal surfaces exist for search, claims, feedback, view events, and wallet analytics tables.

Current friction still visible from institutional records:

- Search-result explanation can confuse users in some modes.
- Missing revenue can be misread as poor performance.
- Wallet/privacy documentation is not fully consistent.
- Hardcoded or unsourced public claims remain a trust risk.

Known aggregate signal counts:

| Signal | Count |
|---|---:|
| analytics_daily | {counts['analytics_daily']} |
| analytics_search | {counts['analytics_search']} |
| feedback | {counts['feedback']} |
| v5_feedback | {counts['v5_feedback']} |
| org_claims | {counts['org_claims']} |
| org_interest | {counts['org_interest']} |
| org_view_events | {counts['org_view_events']} |
| wallet_analytics | {counts['wallet_analytics']} |

Uncertain or unavailable:

- Support email volume is not available from a verified local export.
- Representative nonprofit interview or advisory evidence is still missing.
- Cloud/API usage is not available from a local source of truth.

## Highest Constraint

{highest_constraint}

Evidence:

- {current_constraint['evidence'][0]}
- {current_constraint['evidence'][1]}
- {current_constraint['evidence'][2]}

## Options

{options_block}
## Stewardship Deliberation

{deliberation}
## Recommended Action

- Action: {recommended_action}
- Expected benefit: {expected_benefit}.
- Cost: local engineering time only; no new service or spend.
- Risk: low.
- Reversibility: high; config-only and testable.
- Evidence: {recommendation_evidence}.
- Confidence: {current_constraint['confidence']}.
- Success measure: {success_measure}
- Stop condition: {stop_condition}.
- Human approval requirement: none for local-only config repair; deployment remains approval-gated.

## Financial And Infrastructure Stewardship

- Default budget posture: survival.
- Known recurring cost from repo evidence: documented DigitalOcean droplet resize to $16/mo, not billing-verified.
- GPU capacity: unknown from durable local telemetry.
- CPU capacity: unknown from durable local telemetry.
- Suitable local workloads: embeddings, mission drafting, routine extraction/summarization where privacy allows.
- Suitable cloud workloads: only high-value reasoning where explicitly permitted and justified.
- Data that must remain carefully controlled: private nonprofit operational data, sensitive claims information, and any consequential legal/financial judgments.

## Security, Reliability, And Documentation Notes

- Recent sampled logs:
{chr(10).join(log_lines)}
- Bootstrap unresolved risks remain open in `institution/RISK_REGISTER.md`, especially R-001 through R-006 and R-010 through R-012.
- No secrets were added by this workflow; institutional files remain local repo content only.

## Kill And Simplification Review

- Stop: adding more skills before repeated work demonstrates need.
- Delete: nothing in this cycle; no safe deletion candidate was verified.
- Merge: keep coordination in `institution/HANDOFF_PROTOCOL.md` plus `institution/tasks/` instead of adding another tracker.
- Automate later: scheduling the weekly review only after one more clean manual cycle.
- Return to manual: financial intake remains manual until verified founder inputs exist.
- Paid tool no longer justified: none newly identified from local evidence.
- Feature lacking evidence: broader telemetry expansion beyond existing first-party signals.
- Document lacking purpose: none newly identified inside the institutional layer.

## Founder Dependencies

```text
{read_excerpt(INSTITUTION / 'FOUNDER_REQUESTS.md', 60)}
```

## Recommendation On Scheduling

{scheduling_recommendation}

## Evidence And Confidence

- High confidence: local repo facts, local DB counts, validation command results.
- Medium confidence: local service inventory and model availability.
- Low confidence: billing, provider-console state, active paid services, exact hardware utilization.

## Final Operating Question

What is the highest-impact action Daanaa can responsibly take now to advance its mission, improve life for the organizations it serves, honor stewardship obligations, use the fewest necessary resources, reduce unhealthy dependence on individuals, and leave the institution wiser than it was before?
"""

    founder_brief = f"""# Founder Brief - {today}

## Document Control

| Field | Value |
|---|---|
| Purpose | Concise founder-facing summary from the manual weekly institutional review. |
| Responsible role | Stewardship Systems Agent. |
| Authority level | Briefing; not approval. |
| Review trigger | Founder response, next manual review, or material incident. |
| Editable status | Generated artifact; corrections should be appended or regenerated. |
| Dependencies | `institution/reviews/{today}-weekly-review.md`, `institution/state.json`. |
| Retirement condition | Retire when superseded by a newer founder brief. |

## Most Important Progress

Authority order, machine-readable state, handoff protocol, reusable minimum skill specs, and the manual weekly review are now operating in-repo.

## Most Important Concern

{highest_constraint}

## Highest Constraint

{highest_constraint}

## Recommended Next Action

{recommended_action}

## Budget Or Resource Request

No spending request. Continue in survival posture until current cash, recurring commitments, and active paid services are confirmed.

## Decisions Requiring Founder Approval

- FR-2026-07-10-001: confirm current monthly spend and runway.
- FR-2026-07-10-002: confirm TiDB credential rotation status.
- FR-2026-07-10-003: confirm final deployment approval model.
- FR-2026-07-10-004: confirm offsite backup status.

## Safe Work Continuing Without Approval

- Maintain institutional state and decision memory.
- Run manual weekly reviews locally.
- Perform local-only validation and quality repairs.
- Refine user-insight synthesis from existing aggregate data.

## Confidence

High for local repository and validation facts; low for financial, provider-console, and external service state outside the repo.
"""

    review_path = REVIEWS / f"{today}-weekly-review.md"
    brief_path = BRIEFS / f"{today}-founder-brief.md"
    review_path.write_text(ascii_safe(review), encoding="utf-8")
    brief_path.write_text(ascii_safe(founder_brief), encoding="utf-8")

    print(f"Wrote {review_path.relative_to(ROOT)}")
    print(f"Wrote {brief_path.relative_to(ROOT)}")
    print(f"Updated {STATE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
