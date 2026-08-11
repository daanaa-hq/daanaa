#!/usr/bin/env python3
"""Generate a Codex-ready handoff packet from a task record.

This script is read-only. It extracts task metadata, pass criteria, evidence,
and handoff notes, then flags mismatches between claimed status and what the
record actually proves. It can also write a compact checkpoint JSON so Claude
and Codex can resume from repo state instead of chat history.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

CHECKBOX_RE = re.compile(r"^\s*- \[( |x|X)\] (.+)$")
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
SUBSECTION_RE = re.compile(r"^###\s+(.+?)\s*$")
TASK_DIR = Path("institution/tasks")
SHARED_SKILL = Path("institution/skills/quality-design-operating-model.md")
STATUS_PRIORITY = {
    "in_progress": 0,
    "waiting_review": 1,
    "ready": 2,
    "conditional": 3,
    "pass_with_conditions": 3,
    "completed": 4,
    "complete": 4,
    "pass": 4,
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_status(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = value.replace("✅", "").replace("⚠️", "")
    value = value.replace(" ", "_")
    return value


def parse_task_record(text: str) -> dict:
    result = {
        "title": None,
        "fields": {},
        "sections": {},
        "checkboxes": {},
        "raw_lines": text.splitlines(),
    }

    current_section = None
    current_lines: list[str] = []
    current_subsection = None
    subsection_lines: list[str] = []

    def flush_subsection() -> None:
        nonlocal current_subsection, subsection_lines
        if current_subsection is not None:
            section = result["sections"].setdefault(current_section, {})
            section[current_subsection] = "\n".join(subsection_lines).strip()
            current_subsection = None
            subsection_lines = []

    def flush_section() -> None:
        nonlocal current_section, current_lines
        if current_section is not None and current_subsection is None:
            result["sections"][current_section] = "\n".join(current_lines).strip()
        current_section = None
        current_lines = []

    for line in result["raw_lines"]:
        if line.startswith("# ") and result["title"] is None:
            result["title"] = line[2:].strip()
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            flush_subsection()
            flush_section()
            current_section = section_match.group(1).strip()
            current_lines = []
            continue

        subsection_match = SUBSECTION_RE.match(line)
        if subsection_match and current_section is not None:
            flush_subsection()
            current_subsection = subsection_match.group(1).strip()
            subsection_lines = []
            continue

        if current_subsection is not None:
            subsection_lines.append(line)
            continue

        if current_section is not None:
            current_lines.append(line)
            checkbox_match = CHECKBOX_RE.match(line)
            if checkbox_match:
                result["checkboxes"].setdefault(current_section, []).append(
                    {"checked": checkbox_match.group(1).lower() == "x", "text": checkbox_match.group(2).strip()}
                )
            continue

        table_match = TABLE_ROW_RE.match(line)
        if table_match:
            key = table_match.group(1).strip()
            value = table_match.group(2).strip()
            if key not in {"Field", "---"} and key.strip("-"):
                result["fields"][key] = value

    flush_subsection()
    flush_section()
    return result


def latest_task_record() -> Path:
    candidates = [path for path in TASK_DIR.glob("*.md") if path.is_file() and path.name.lower() != "readme.md"]
    if not candidates:
        raise FileNotFoundError(f"no task records found in {TASK_DIR}")

    def score(path: Path) -> tuple[int, float, str]:
        try:
            parsed = parse_task_record(read_text(path))
            priority = STATUS_PRIORITY.get(normalize_status(parsed["fields"].get("Status")), 5)
        except Exception:
            priority = 9
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        return (priority, -mtime, path.name)

    return sorted(candidates, key=score)[0]


def find_section_text(sections: dict, names: Iterable[str]) -> str:
    for name in names:
        if name in sections:
            section = sections[name]
            if isinstance(section, str):
                return section
            if isinstance(section, dict):
                return "\n".join(section.values())
    return ""


def section_has(text: str, needles: Iterable[str]) -> bool:
    lower = text.lower()
    return all(needle.lower() in lower for needle in needles)


def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ", "• ")):
            return stripped[2:].strip()
        if stripped[0].isdigit() and "." in stripped[:3]:
            return stripped.split(" ", 1)[1].strip() if " " in stripped else stripped
        return stripped
    return ""


def extract_status(text: str) -> str:
    if not text:
        return ""
    return normalize_status(text)


def analyze(task: dict, task_path: Path) -> dict:
    fields = task["fields"]
    sections = task["sections"]
    checkboxes = task["checkboxes"]
    title = task["title"] or fields.get("Identifier") or "Unknown task"

    pass_criteria = find_section_text(sections, ["PASS Criteria (Exact)", "PASS Criteria", "Acceptance Criteria"])
    evidence = find_section_text(sections, ["Evidence Summary", "Evidence & Validation", "Validation", "Benchmark Results (COMPLETED)"])
    handoff = find_section_text(sections, ["Handoff to Codex", "Handoff Checklist (for Codex)", "Handoff"])
    next_action_blob = find_section_text(sections, ["Open follow-up", "Work Queue (Priority Order)", "Next", "Closeout"])

    issues = []
    if pass_criteria and section_has(pass_criteria, ["p50", "p95"]):
        if not section_has(evidence, ["p50", "p95"]):
            issues.append("PASS criteria require p50/p95, but evidence section does not document them.")
    if pass_criteria and "query-level" in pass_criteria.lower():
        if not section_has(evidence, ["query-level"]):
            issues.append("PASS criteria require query-level results, but evidence section does not document them.")
    if pass_criteria and "http 500" in pass_criteria.lower():
        if not section_has(evidence, ["http 500"]):
            issues.append("PASS criteria mention HTTP 500, but evidence section does not show the absence/presence clearly.")

    checklist = checkboxes.get("Handoff Checklist (for Codex)", [])
    open_checklist = [item["text"] for item in checklist if not item["checked"]]

    status = fields.get("Status", "unknown")
    normalized_status = extract_status(status)
    verdict = "pass" if ("pass" in normalized_status or "completed" in normalized_status) else "review"
    if issues:
        verdict = "conditional"

    next_action = first_meaningful_line(next_action_blob) or first_meaningful_line(handoff)
    claude_perspective = " ".join(
        part for part in [
            f"Implementer lens: {next_action or 're-read the task record and evidence'}.",
            "Checkpoint what changed and what is still uncertain.",
        ] if part
    )
    codex_perspective = " ".join(
        part for part in [
            "Reviewer lens: verify the claimed status against explicit evidence.",
            "Call out missing proof, hidden coupling, or authority gaps.",
        ] if part
    )
    resume_prompt = " ".join(
        part for part in [
            f"Resume task {fields.get('Identifier', title)}.",
            f"Owner: {fields.get('Owner', 'unknown')}.",
            f"Scope: {fields.get('Scope', 'unknown')}.",
            f"Next: {next_action or 're-read the task record and evidence'}.",
        ] if part
    )

    try:
        git_head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        git_head = None

    return {
        "title": title,
        "fields": fields,
        "issues": issues,
        "open_checklist": open_checklist,
        "verdict": verdict,
        "pass_criteria": pass_criteria,
        "evidence": evidence,
        "handoff": handoff,
        "next_action": next_action,
        "claude_perspective": claude_perspective,
        "codex_perspective": codex_perspective,
        "resume_prompt": resume_prompt,
        "shared_skill": str(SHARED_SKILL),
        "git_head": git_head,
        "task_path": str(task_path),
        "status_raw": status,
    }


def build_packet(task_path: Path, analysis: dict) -> str:
    fields = analysis["fields"]
    lines: list[str] = []
    lines.append(f"# Codex Handoff Packet: {analysis['title']}")
    lines.append("")
    lines.append("## Task Metadata")
    lines.append(f"- Task file: `{task_path}`")
    if fields.get("Owner"):
        lines.append(f"- Owner: {fields['Owner']}")
    if fields.get("Scope"):
        lines.append(f"- Scope: {fields['Scope']}")
    if fields.get("Affected paths"):
        lines.append(f"- Affected paths: {fields['Affected paths']}")
    if fields.get("Authority constraints"):
        lines.append(f"- Authority constraints: {fields['Authority constraints']}")
    if fields.get("Status"):
        lines.append(f"- Status: {fields['Status']}")
    if analysis.get("git_head"):
        lines.append(f"- Git HEAD: {analysis['git_head']}")
    if analysis.get("shared_skill"):
        lines.append(f"- Shared skill: `{analysis['shared_skill']}`")
    lines.append("- Startup protocol: `institution/handoffs/STARTUP_PROTOCOL.md`")
    lines.append("")
    lines.append("## Verdict")
    lines.append(f"- Automation verdict: **{analysis['verdict'].upper()}**")
    if analysis["issues"]:
        lines.append("- Mismatches detected:")
        for issue in analysis["issues"]:
            lines.append(f"  - {issue}")
    else:
        lines.append("- No pass/evidence mismatches detected in the task record.")
    if analysis["next_action"]:
        lines.append(f"- Next action: {analysis['next_action']}")
    if analysis["open_checklist"]:
        lines.append("- Open handoff checklist items:")
        for item in analysis["open_checklist"]:
            lines.append(f"  - {item}")
    lines.append("")
    lines.append("## Perspective Split")
    lines.append(f"- Claude: {analysis['claude_perspective']}")
    lines.append(f"- Codex: {analysis['codex_perspective']}")
    lines.append("")
    lines.append("## What Codex Should Verify")
    lines.append("1. The task status matches the evidence, not just the label.")
    lines.append("2. The declared pass criteria are all explicitly evidenced.")
    lines.append("3. Any missing latency, query-level, or HTTP-failure data is called out.")
    lines.append("4. The handoff target and next owner are unambiguous.")
    lines.append("")
    if analysis["pass_criteria"]:
        lines.append("## Extracted PASS Criteria")
        lines.append(analysis["pass_criteria"].strip())
        lines.append("")
    if analysis["evidence"]:
        lines.append("## Extracted Evidence")
        lines.append(analysis["evidence"].strip())
        lines.append("")
    if analysis["handoff"]:
        lines.append("## Extracted Handoff Notes")
        lines.append(analysis["handoff"].strip())
        lines.append("")
    lines.append("## Resume Hint")
    lines.append(analysis["resume_prompt"])
    if analysis.get("shared_skill"):
        lines.append("")
        lines.append("## Relevant Shared Skill")
        lines.append(f"`{analysis['shared_skill']}`")
    lines.append("")
    lines.append("## Suggested Codex Reply")
    lines.append("- Findings first, ordered by severity")
    lines.append("- Exact file references")
    lines.append("- Residual risks or missing tests")
    lines.append("- Ready to merge, conditional, or needs another pass")
    return "\n".join(lines).rstrip() + "\n"


def build_checkpoint(analysis: dict) -> dict:
    fields = analysis["fields"]
    return {
        "task_file": analysis["task_path"],
        "title": analysis["title"],
        "verdict": analysis["verdict"],
        "status": analysis["status_raw"],
        "git_head": analysis.get("git_head"),
        "owner": fields.get("Owner"),
        "scope": fields.get("Scope"),
        "affected_paths": fields.get("Affected paths"),
        "authority_constraints": fields.get("Authority constraints"),
        "next_action": analysis.get("next_action"),
        "claude_perspective": analysis.get("claude_perspective"),
        "codex_perspective": analysis.get("codex_perspective"),
        "resume_prompt": analysis.get("resume_prompt"),
        "shared_skill": analysis.get("shared_skill"),
        "startup_protocol": "institution/handoffs/STARTUP_PROTOCOL.md",
        "issues": analysis["issues"],
        "open_checklist": analysis["open_checklist"],
        "pass_criteria": analysis["pass_criteria"],
        "evidence": analysis["evidence"],
        "handoff": analysis["handoff"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Codex-ready handoff packet from a task record")
    parser.add_argument("task", nargs="?", type=Path, help="Path to the task record markdown file")
    parser.add_argument("--latest", action="store_true", help="Auto-select the latest active task record")
    parser.add_argument("--out", type=Path, help="Write packet to this file instead of stdout")
    parser.add_argument("--checkpoint-out", type=Path, help="Write a compact JSON checkpoint for resuming later")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary instead of markdown")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if mismatches are detected")
    args = parser.parse_args()

    task_path = args.task
    if args.latest:
        task_path = latest_task_record()
    if task_path is None:
        parser.error("task path required unless --latest is used")

    parsed = parse_task_record(read_text(task_path))
    analysis = analyze(parsed, task_path)
    checkpoint = build_checkpoint(analysis)

    if args.checkpoint_out:
        args.checkpoint_out.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    if args.json:
        output = json.dumps(checkpoint, indent=2)
    else:
        output = build_packet(task_path, analysis)

    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    if args.check and analysis["issues"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
