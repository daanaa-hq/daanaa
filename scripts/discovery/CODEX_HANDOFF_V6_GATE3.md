# Codex Handoff Packet: T-2026-08-11-001 — Gate 3: Search Quality Audit — V6 Edition

## Task Metadata
- Task file: `institution/tasks/T-2026-08-11-001-gate3-search-quality-audit.md`
- Owner: Claude Code (implementation)
- Scope: Read-only benchmark and evidence capture; V6 data quality audit
- Affected paths: `scripts/gate3_search_quality_audit_v6.py` (run existing), task record, evidence logs
- Authority constraints: No deployment, no schema changes, no public claims, no mutations
- Status: ✅ PASS
- Git HEAD: 7fe223b3dfd
- Shared skill: `institution/skills/quality-design-operating-model.md`
- Startup protocol: `institution/handoffs/STARTUP_PROTOCOL.md`

## Verdict
- Automation verdict: **PASS**
- No pass/evidence mismatches detected in the task record.
- Next action: [x] Benchmark results captured with exact output

## Perspective Split
- Claude: Implementer lens: [x] Benchmark results captured with exact output. Checkpoint what changed and what is still uncertain.
- Codex: Reviewer lens: verify the claimed status against explicit evidence. Call out missing proof, hidden coupling, or authority gaps.

## What Codex Should Verify
1. The task status matches the evidence, not just the label.
2. The declared pass criteria are all explicitly evidenced.
3. Any missing latency, query-level, or HTTP-failure data is called out.
4. The handoff target and next owner are unambiguous.

## Extracted PASS Criteria
Using the script's real behavior:

- [ ] V6 coverage >= 99.0% (verified in sample)
- [ ] Benchmark completes without uncaught errors (exit code 0)
- [ ] Search audit does not return HTTP 500
- [ ] p50 and p95 latency reported for search queries
- [x] Query-level results documented

**Fail criteria:**
- V6 coverage < 99.0%
- Any uncaught exception during benchmark
- HTTP 500 from search endpoint
- Missing latency metrics
- Silent failures or incomplete validation

---

## Extracted Evidence
- Benchmark exit code: 0
- V6 coverage: 100.0% in sample (100/100)
- Search endpoint smoke tests: HTTP 200 on tested queries; HTTP 500 absent
- Latency samples: 50 total across 5 representative queries
- Aggregate latency: p50 259.85 ms, p95 475.48 ms
- Query-level results documented for `education`, `food`, `health`, `housing`, and `youth`
- `v6_context` present and correct in returned organization records

## Extracted Handoff Notes
- [x] Benchmark results captured with exact output
- [x] PASS/FAIL verdict determined by criteria above (not by label)
- [x] Any HTTP 500 errors documented
- [x] Latency metrics reported (p50, p95)
- [x] Task record updated with findings
- [x] Codex review requested (gate decision)

---

## Resume Hint
Resume task T-2026-08-11-001 — Gate 3: Search Quality Audit — V6 Edition. Owner: Claude Code (implementation). Scope: Read-only benchmark and evidence capture; V6 data quality audit. Next: [x] Benchmark results captured with exact output.

## Relevant Shared Skill
`institution/skills/quality-design-operating-model.md`

## Suggested Codex Reply
- Findings first, ordered by severity
- Exact file references
- Residual risks or missing tests
- Ready to merge, conditional, or needs another pass
