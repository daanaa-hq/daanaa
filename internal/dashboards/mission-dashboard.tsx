// Mission Dashboard — Public impact view
// Audience: public (advisors, donors, nonprofits, press)
// Auth: none
// Refresh: revalidate every 24 hours

export const revalidate = 86400;

async function getMissionData() {
  // TODO: parse from meritgiving-ops markdown + filtered Postgres queries

  return {
    heroStats: {
      einsCovered: 1800000, // updated monthly from IRS BMF
      lastDataRefresh: "2026-05-13",
      message: "All 501(c)(3)s. Equally.",
    },
    phase1Stats: {
      profilesClaimed: 0,
      activeNonprofits30d: 0,
      tipsCollectedTotal: 0,
    },
    phase2Stats: {
      dollarsSavedAggregate: 0,
      vendorPartnerships: 0,
      hoursSavedAggregate: 0,
    },
    buildLog: [
      {
        date: "2026-05-19",
        title: "Day 1: Parallel execution begins",
        excerpt: "Building MERIT in public. Today: account signups, credit applications, org scaffolding.",
        url: "/blog/day-1",
      },
    ],
    recentDecisions: [
      {
        id: "ADR-001",
        date: "2026-05-19",
        title: "Operate as DBA under EcoMargins LLC until MeritGiving LLC forms",
        summary: "Speed matters; LLC paperwork is mechanical. Clean transfer when ready.",
      },
    ],
    sectorReports: [],
    missionPrinciples: [
      "MERIT never holds donor money in Phase 0",
      "MERIT treats all 501(c)(3)s equally",
      "MERIT data is sourced from IRS public records",
      "MERIT never charges nonprofits for core services",
      "MERIT publishes transparently",
      "MERIT acknowledges its limits",
      "MERIT defers to professionals on regulated matters",
      "MERIT prioritizes long-term trust over short-term growth",
    ],
  };
}

export default async function MissionDashboard() {
  const data = await getMissionData();

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-12">
      {/* Hero */}
      <section className="text-center py-12 border-b">
        <h1 className="text-4xl font-semibold">MERIT</h1>
        <p className="text-lg text-gray-600 mt-2">{data.heroStats.message}</p>
        <div className="mt-8 inline-flex items-baseline gap-2">
          <span className="text-5xl font-bold">
            {data.heroStats.einsCovered.toLocaleString()}
          </span>
          <span className="text-gray-500">501(c)(3)s in directory</span>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          IRS data as of {data.heroStats.lastDataRefresh}
        </p>
      </section>

      {/* Phase 1 stats (visible when meaningful) */}
      {(data.phase1Stats.profilesClaimed > 0 ||
        data.phase1Stats.tipsCollectedTotal > 0) && (
        <section>
          <h2 className="text-xl font-semibold mb-4">Activity</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-6 bg-gray-50 rounded-lg">
              <div className="text-3xl font-semibold">
                {data.phase1Stats.profilesClaimed.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 mt-1">Profiles claimed</div>
            </div>
            <div className="p-6 bg-gray-50 rounded-lg">
              <div className="text-3xl font-semibold">
                {data.phase1Stats.activeNonprofits30d.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 mt-1">Active in last 30 days</div>
            </div>
            <div className="p-6 bg-gray-50 rounded-lg">
              <div className="text-3xl font-semibold">
                ${data.phase1Stats.tipsCollectedTotal.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500 mt-1">Total tips (transparency)</div>
            </div>
          </div>
        </section>
      )}

      {/* Build log */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Build log</h2>
        <ul className="space-y-4">
          {data.buildLog.map((post) => (
            <li key={post.url} className="border-b pb-4">
              <div className="text-xs text-gray-400">{post.date}</div>
              <a
                href={post.url}
                className="text-lg font-medium hover:underline block mt-1"
              >
                {post.title}
              </a>
              <p className="text-gray-600 mt-1">{post.excerpt}</p>
            </li>
          ))}
        </ul>
        <a href="/blog" className="text-sm text-blue-600 hover:underline mt-4 inline-block">
          See all posts →
        </a>
      </section>

      {/* Recent decisions */}
      <section>
        <h2 className="text-xl font-semibold mb-4">How we decide</h2>
        <p className="text-gray-600 mb-4">
          Every meaningful decision lives in our public decision log.
        </p>
        <ul className="space-y-3">
          {data.recentDecisions.map((adr) => (
            <li key={adr.id} className="p-4 border rounded-lg">
              <div className="flex items-baseline gap-3">
                <span className="text-xs font-mono text-gray-400">{adr.id}</span>
                <span className="text-xs text-gray-400">{adr.date}</span>
              </div>
              <div className="font-medium mt-1">{adr.title}</div>
              <p className="text-sm text-gray-600 mt-1">{adr.summary}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Mission principles */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Mission lock</h2>
        <p className="text-gray-600 mb-4">
          These principles are non-negotiable. They're encoded in our operating agreement.
        </p>
        <ol className="space-y-2 list-decimal list-inside">
          {data.missionPrinciples.map((p, i) => (
            <li key={i} className="text-gray-700">
              {p}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
