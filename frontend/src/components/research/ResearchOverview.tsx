interface ResearchOverviewProps {
  sessionToken: string
  metadata: any
}

export default function ResearchOverview({
  sessionToken,
  metadata,
}: ResearchOverviewProps) {
  return (
    <div>
      <h1 className="text-4xl font-display text-deep-navy mb-4">
        Daanaa Research Dashboard
      </h1>
      <p className="text-lg text-cool-grey mb-6 max-w-2xl">
        A guide to how Daanaa discovers, organizes, and provides peer
        financial context for nonprofit organizations. This research document is
        intended for advisors, academics, foundations, and nonprofit professionals
        seeking to understand our methodology.
      </p>

      {metadata && (
        <div className="grid grid-cols-3 gap-4 mt-8">
          <div className="bg-soft-gold/10 rounded-lg p-4">
            <div className="text-3xl font-display text-link-gold">
              {(metadata.total_organizations / 1_000_000).toFixed(1)}M
            </div>
            <div className="text-sm text-cool-grey">Organizations indexed</div>
          </div>
          <div className="bg-soft-gold/10 rounded-lg p-4">
            <div className="text-3xl font-display text-link-gold">50</div>
            <div className="text-sm text-cool-grey">States represented</div>
          </div>
          <div className="bg-soft-gold/10 rounded-lg p-4">
            <div className="text-3xl font-display text-link-gold">v6</div>
            <div className="text-sm text-cool-grey">Current context system</div>
          </div>
        </div>
      )}

      <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-deep-navy mb-2">What this research covers</h3>
        <ul className="space-y-2 text-sm text-cool-grey">
          <li>How we source and verify nonprofit data</li>
          <li>How v6 forms reasonable peer context groups</li>
          <li>Reported, peer-reference, and limited context</li>
          <li>How we describe uncertainty and coverage</li>
          <li>What changed across scoring versions</li>
        </ul>
      </div>
    </div>
  )
}
