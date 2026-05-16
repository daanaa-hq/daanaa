# MERITGIVING NIGHTLY DATA AUDIT — Agent Task

## Context
You are the MeritGiving data pipeline agent running on ecomargins (RX 7900 XTX, Ubuntu).
Database: ~/meritgiving/data/merit_registry.db
Telegram bot: MeritGivingBot (notify on completion/failure)

## Objective
Run a nightly quality audit on the nonprofit registry and produce a summary report.

## Steps
1. Connect to SQLite DB at ~/meritgiving/data/merit_registry.db
2. Run these checks:
   - Total org count in registry_enriched
   - Orgs with revenue = 0 (flag for follow-up)
   - Orgs missing NTEE category
   - Duplicate EINs across tables
   - Latest IRS BMF sync date
3. Generate a markdown report with:
   - Date/time stamp
   - Row counts per table
   - Flagged issues with counts
   - Top 5 largest orgs by revenue
4. Save report to ~/meritgiving/reports/nightly_$(date +%Y%m%d).md
5. Send Telegram notification with summary + file path

## Constraints
- Use local Ollama (qwen2.5-coder:32b) for any reasoning steps
- Do NOT modify data — read-only audit
- If DB is locked, wait 60s and retry once
- Log all commands to session for audit trail

## Output Format
=== MERITGIVING NIGHTLY AUDIT ===
Date: 2026-05-14
Registry: X orgs
Issues: Y flagged
Status: PASS / WARN / FAIL
Report: /home/akbar/meritgiving/reports/nightly_20260514.md
