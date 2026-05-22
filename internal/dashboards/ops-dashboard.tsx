// Ops Dashboard — Operational view
// Audience: Akbar + Claude agents
// Auth: Clerk-gated
// Refresh: revalidate every 60 sec

import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export const revalidate = 60;

async function getOpsData() {
  // TODO: wire to actual data sources
  // - Better Stack API (uptime)
  // - Sentry API (errors)
  // - Cloudflare API (WAF events)
  // - Stripe API (tip jar)
  // - n8n API (workflows)
  // - Anthropic Console (manual entry until API)

  return {
    production: {
      uptime24h: 100,
      uptime7d: 100,
      uptime30d: 100,
      errorRatePercent: 0,
      p95ResponseMs: 0,
      wafEventsLast24h: 0,
    },
    tipJar: {
      thisMonth: 0,
      thisWeek: 0,
      latestAmount: null as number | null,
      payoutStatus: "no_payouts_yet" as const,
    },
    aiUsage: {
      claudeMonthlySpend: 0,
      credits: [
        { provider: "AWS Activate", balance: 0, expires: null },
        { provider: "Google Startups", balance: 0, expires: null },
        { provider: "Cloudflare", balance: 0, expires: null },
        { provider: "Microsoft Founders Hub", balance: 0, expires: null },
        { provider: "Anthropic Startup", balance: 0, expires: null },
      ],
    },
    inbox: {
      nonprofits: 0,
      support: 0,
      legal: 0,
      security: 0,
      partners: 0,
      press: 0,
      approvalQueue: 0,
    },
    workflows: {
      n8nLastSuccess: null,
      lastBackup: null,
      lastBmfRefresh: null,
      lastBadgeRecalc: null,
    },
  };
}

function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="p-4 bg-white border rounded-lg">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

export default async function OpsDashboard() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const data = await getOpsData();

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-baseline justify-between border-b pb-4">
        <h1 className="text-2xl font-semibold">MERIT — Ops Dashboard</h1>
        <span className="text-sm text-gray-500">refresh: 60s</span>
      </div>

      {/* Production health */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Production health</h2>
        <div className="grid grid-cols-4 gap-3">
          <MetricCard label="Uptime 24h" value={`${data.production.uptime24h}%`} />
          <MetricCard label="Uptime 7d" value={`${data.production.uptime7d}%`} />
          <MetricCard label="Error rate" value={`${data.production.errorRatePercent}%`} />
          <MetricCard label="P95 response" value={`${data.production.p95ResponseMs}ms`} />
        </div>
      </section>

      {/* Tip jar */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Tip jar</h2>
        <div className="grid grid-cols-3 gap-3">
          <MetricCard label="This month" value={`$${data.tipJar.thisMonth}`} />
          <MetricCard label="This week" value={`$${data.tipJar.thisWeek}`} />
          <MetricCard
            label="Latest tip"
            value={data.tipJar.latestAmount ? `$${data.tipJar.latestAmount}` : "—"}
          />
        </div>
      </section>

      {/* AI usage */}
      <section>
        <h2 className="text-lg font-semibold mb-3">AI usage & credits</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <MetricCard
            label="Claude API spend this month"
            value={`$${data.aiUsage.claudeMonthlySpend}`}
          />
          <div className="p-4 bg-white border rounded-lg">
            <div className="text-xs text-gray-500 mb-2">Credits balance</div>
            <ul className="space-y-1 text-sm">
              {data.aiUsage.credits.map((c) => (
                <li key={c.provider} className="flex justify-between">
                  <span className="text-gray-600">{c.provider}</span>
                  <span className="font-mono">${c.balance}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Inbox */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Inbox queues</h2>
        <div className="grid grid-cols-4 gap-3">
          <MetricCard label="nonprofits@" value={data.inbox.nonprofits} />
          <MetricCard label="support@" value={data.inbox.support} />
          <MetricCard label="legal@" value={data.inbox.legal} />
          <MetricCard label="security@" value={data.inbox.security} />
          <MetricCard label="partners@" value={data.inbox.partners} />
          <MetricCard label="press@" value={data.inbox.press} />
          <MetricCard
            label="Approval queue"
            value={data.inbox.approvalQueue}
            sub="awaiting CEO"
          />
        </div>
      </section>

      {/* Workflows */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Workflow health</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <MetricCard
            label="Last n8n success"
            value={data.workflows.n8nLastSuccess ?? "—"}
          />
          <MetricCard label="Last backup" value={data.workflows.lastBackup ?? "—"} />
          <MetricCard
            label="Last BMF refresh"
            value={data.workflows.lastBmfRefresh ?? "—"}
          />
          <MetricCard
            label="Last badge recalc"
            value={data.workflows.lastBadgeRecalc ?? "—"}
          />
        </div>
      </section>
    </div>
  );
}
