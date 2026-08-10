// CEO Dashboard — Executive view
// Auth: Clerk-gated in production; skipped locally when CLERK_SECRET_KEY is unset
// Refresh: revalidate every 5 minutes

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getOpsState } from "@/lib/ops-state";
import type { GateStatus, RiskSeverity, RiskStatus, SystemStatus } from "@/lib/ops-state";

export const revalidate = 300;

// ── Auth gate (skipped when Clerk keys not configured) ────────────────────────
async function checkAuth() {
  if (!process.env.CLERK_SECRET_KEY) return; // dev / no-Clerk mode
  const { auth } = await import("@clerk/nextjs/server");
  const { redirect } = await import("next/navigation");
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");
}

// ── Visual helpers ────────────────────────────────────────────────────────────
function StatusDot({ status }: { status: SystemStatus }) {
  const colors: Record<SystemStatus, string> = {
    green: "bg-emerald-500",
    yellow: "bg-amber-400",
    red: "bg-red-500",
  };
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${colors[status]}`} />;
}

function GatePill({ status }: { status: GateStatus }) {
  const map: Record<GateStatus, { label: string; cls: string }> = {
    complete:    { label: "Complete",     cls: "bg-emerald-100 text-emerald-800" },
    in_progress: { label: "In progress",  cls: "bg-blue-100 text-blue-800" },
    blocked:     { label: "Blocked",      cls: "bg-red-100 text-red-800" },
    upcoming:    { label: "Upcoming",     cls: "bg-gray-100 text-gray-600" },
  };
  const { label, cls } = map[status];
  return <span className={`text-xs px-2 py-0.5 rounded font-medium ${cls}`}>{label}</span>;
}

function RiskBadge({ severity }: { severity: RiskSeverity }) {
  const map: Record<RiskSeverity, string> = {
    critical: "bg-red-100 text-red-700",
    high:     "bg-orange-100 text-orange-700",
    medium:   "bg-amber-100 text-amber-700",
    low:      "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded font-medium capitalize ${map[severity]}`}>
      {severity}
    </span>
  );
}

function RiskStatusPill({ status }: { status: RiskStatus }) {
  const map: Record<RiskStatus, string> = {
    open:       "bg-red-50 text-red-600",
    mitigating: "bg-amber-50 text-amber-700",
    monitoring: "bg-blue-50 text-blue-600",
    closed:     "bg-gray-50 text-gray-500",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded capitalize ${map[status]}`}>{status}</span>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default async function CEODashboard() {
  await checkAuth();

  const state = getOpsState();
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

      {/* Header */}
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">MERIT — CEO</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{today}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusDot status={state.status} />
          <span className="text-sm font-medium">
            {state.status === "green" ? "All clear" : state.status === "yellow" ? "Watch items" : "Action needed"}
          </span>
        </div>
      </div>

      <Separator />

      {/* Status bar */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Runway</p>
            <p className="text-2xl font-semibold mt-1">{state.runwayMonths} mo</p>
            <p className="text-xs text-muted-foreground mt-0.5">Update when CPA confirms</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Phase</p>
            <p className="text-2xl font-semibold mt-1">Phase 0</p>
            <p className="text-xs text-muted-foreground mt-0.5">Directory + Badges</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">
              Gate {state.currentGate.number} — {state.currentGate.name}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-2xl font-semibold">Week {state.currentGate.week}</p>
              <GatePill status={state.currentGate.status} />
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">of 24-week build plan</p>
          </CardContent>
        </Card>
      </div>

      {/* KPIs */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">KPI movement</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            {state.kpis.map((k) => (
              <div key={k.label} className="space-y-1">
                <p className="text-xs text-muted-foreground">{k.label}</p>
                <p className="text-xl font-semibold">{k.value}</p>
                <p className="text-xs text-muted-foreground">target: {k.target}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">

        {/* Top risks */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Top risks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {state.topRisks.map((r) => (
              <div key={r.id} className="flex items-center gap-2 py-1.5 border-b last:border-0">
                <span className="text-xs font-mono text-muted-foreground w-12">{r.id}</span>
                <span className="flex-1 text-sm">{r.title}</span>
                <RiskBadge severity={r.severity} />
                <RiskStatusPill status={r.status} />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Last session */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Last session — {state.lastSession.date}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground leading-relaxed">
              {state.lastSession.headline}
            </p>
            {state.lastSession.nextUp.length > 0 && (
              <div>
                <p className="text-xs font-medium mb-1.5">Up next:</p>
                <ul className="space-y-1">
                  {state.lastSession.nextUp.map((item, i) => (
                    <li key={i} className="text-sm flex gap-2">
                      <span className="text-muted-foreground">{i + 1}.</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

      </div>

      {/* Data freshness note */}
      <p className="text-xs text-muted-foreground text-right">
        Reads from <code className="text-xs">meritgiving-ops/</code> state files · refreshes every 5 min
      </p>
    </div>
  );
}
