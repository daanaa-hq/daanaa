/**
 * Reads live operational state from meritgiving-ops/ markdown files.
 * Falls back to hardcoded snapshot when files aren't on disk (Vercel).
 *
 * Local path: ../../../meritgiving-ops relative to process.cwd() (apps/web)
 * Override:   OPS_STATE_DIR env var
 */

import fs from "fs";
import path from "path";

const OPS_DIR =
  process.env.OPS_STATE_DIR ||
  path.join(process.cwd(), "../../../meritgiving-ops");

function readFile(relPath: string): string | null {
  try {
    return fs.readFileSync(path.join(OPS_DIR, relPath), "utf-8");
  } catch {
    return null;
  }
}

// ── Phase / Gate ─────────────────────────────────────────────────────────────

export type GateStatus = "complete" | "in_progress" | "blocked" | "upcoming";

export interface CurrentGate {
  number: number;
  name: string;
  week: number;
  status: GateStatus;
}

export function getCurrentGate(): CurrentGate {
  // Compute week number from project start (2026-05-19)
  const start = new Date("2026-05-19");
  const now = new Date();
  const week = Math.max(1, Math.ceil((now.getTime() - start.getTime()) / (7 * 24 * 60 * 60 * 1000)));

  // Parse phase-plan.md to find current gate
  const raw = readFile("strategy/phase-plan.md");
  if (raw) {
    const gateMatch = raw.match(/\*\*Gate\s+(\d+)\s+\(Week\s+(\d+)\):\s+([^\*\n]+)\*\*/);
    if (gateMatch) {
      const gateWeek = parseInt(gateMatch[2]);
      const status: GateStatus = week >= gateWeek ? "in_progress" : "upcoming";
      return {
        number: parseInt(gateMatch[1]),
        name: gateMatch[3].trim(),
        week,
        status,
      };
    }
  }

  return { number: 1, name: "Legal Foundation", week, status: "in_progress" };
}

// ── Risks ─────────────────────────────────────────────────────────────────────

export type RiskStatus = "open" | "mitigating" | "monitoring" | "closed";
export type RiskSeverity = "critical" | "high" | "medium" | "low";

export interface Risk {
  id: string;
  title: string;
  severity: RiskSeverity;
  status: RiskStatus;
}

export function getTopRisks(limit = 5): Risk[] {
  const raw = readFile("strategy/risks.md");
  if (!raw) return FALLBACK_RISKS.slice(0, limit);

  const risks: Risk[] = [];
  const blocks = raw.split(/(?=###\s+R-\d+)/);

  for (const block of blocks) {
    const idMatch = block.match(/###\s+(R-\d+):\s+(.+)/);
    if (!idMatch) continue;

    const severityMatch = block.match(/\*\*Severity:\*\*\s+(Critical|High|Medium|Low)/i);
    const statusMatch = block.match(/\*\*Status:\*\*\s+(.+)/);

    const rawStatus = (statusMatch?.[1] || "open").toLowerCase();
    const status: RiskStatus =
      rawStatus.includes("mitigat") ? "mitigating"
      : rawStatus.includes("monitor") ? "monitoring"
      : rawStatus.includes("closed") || rawStatus.includes("resolved") ? "closed"
      : "open";

    risks.push({
      id: idMatch[1],
      title: idMatch[2].trim(),
      severity: (severityMatch?.[1].toLowerCase() || "medium") as RiskSeverity,
      status,
    });

    if (risks.length >= limit) break;
  }

  return risks.length ? risks : FALLBACK_RISKS.slice(0, limit);
}

const FALLBACK_RISKS: Risk[] = [
  { id: "R-001", title: "Profile claim fraud", severity: "critical", status: "open" },
  { id: "R-002", title: "Data accuracy errors causing harm", severity: "critical", status: "mitigating" },
  { id: "R-003", title: "Legal action over tip jar framing", severity: "critical", status: "open" },
  { id: "R-004", title: "Security breach exposing PII", severity: "critical", status: "mitigating" },
  { id: "R-005", title: "Founder burnout", severity: "high", status: "monitoring" },
];

// ── KPIs ──────────────────────────────────────────────────────────────────────

export interface KPI {
  label: string;
  value: string | number;
  target: string | number;
  direction: "good" | "warn" | "neutral";
}

export function getKPIs(): KPI[] {
  // KR targets come from OKRs; actuals are tracked manually for now
  const start = new Date("2026-05-19");
  const now = new Date();
  const daysElapsed = Math.floor((now.getTime() - start.getTime()) / (24 * 60 * 60 * 1000));
  const daysToLaunch = Math.max(0, 175 - daysElapsed); // 25 weeks = 175 days

  return [
    { label: "Newsletter subs", value: 0, target: 500, direction: "neutral" },
    { label: "Credits secured", value: "$0", target: "$10K", direction: "neutral" },
    { label: "Monthly burn", value: "$8", target: "<$300", direction: "good" },
    { label: "Days to launch", value: daysToLaunch, target: 175, direction: daysToLaunch > 0 ? "neutral" : "warn" },
  ];
}

// ── Last session summary ───────────────────────────────────────────────────────

export interface SessionSummary {
  date: string;
  headline: string;
  nextUp: string[];
}

export function getLastSession(): SessionSummary {
  const raw = readFile("state/last-session.md");
  if (!raw) {
    return {
      date: "2026-05-19",
      headline: "Build Day 1 complete — scaffolding, departments, and ops structure generated.",
      nextUp: ["Set up GitHub org", "Submit 5 credit applications", "LLC formation kick-off"],
    };
  }

  const dateMatch = raw.match(/# Last Session.*?(\d{4}-\d{2}-\d{2})/);
  const happenedMatch = raw.match(/## What happened\n+(.+)/);
  const nextLines: string[] = [];
  const nextSection = raw.match(/## What's next[^\n]*\n+([\s\S]+?)(?=##|$)/);
  if (nextSection) {
    const bullets = nextSection[1].match(/^[-*]\s+(.+)/gm) || [];
    bullets.slice(0, 4).forEach((b) => nextLines.push(b.replace(/^[-*]\s+/, "")));
  }

  return {
    date: dateMatch?.[1] || "2026-05-19",
    headline: happenedMatch?.[1]?.trim() || "Build in progress.",
    nextUp: nextLines,
  };
}

// ── Overall status ────────────────────────────────────────────────────────────

export type SystemStatus = "green" | "yellow" | "red";

export interface OpsState {
  status: SystemStatus;
  runwayMonths: number;
  currentGate: CurrentGate;
  topRisks: Risk[];
  kpis: KPI[];
  lastSession: SessionSummary;
}

export function getOpsState(): OpsState {
  const risks = getTopRisks(5);
  const openCritical = risks.filter((r) => r.severity === "critical" && r.status === "open").length;
  const status: SystemStatus = openCritical > 2 ? "yellow" : "green";

  return {
    status,
    runwayMonths: 14, // update when CPA confirms
    currentGate: getCurrentGate(),
    topRisks: risks,
    kpis: getKPIs(),
    lastSession: getLastSession(),
  };
}
