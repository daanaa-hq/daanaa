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
            <div className="text-3xl font-display text-link-gold">3</div>
            <div className="text-sm text-cool-grey">Financial Archetypes</div>
          </div>
        </div>
      )}

      <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-deep-navy mb-2">📌 What you'll learn</h3>
        <ul className="space-y-2 text-sm text-cool-grey">
          <li>✓ How we source and verify nonprofit data</li>
          <li>✓ Our peer financial context scoring methodology (v5)</li>
          <li>✓ Three financial archetypes and how they define nonprofit strategy</li>
          <li>✓ Revenue bands and peer group benchmarking</li>
          <li>✓ Health signals and what they reveal about financial sustainability</li>
          <li>✓ Transparency about our data limitations and coverage</li>
        </ul>
      </div>
    </div>
  )
}
