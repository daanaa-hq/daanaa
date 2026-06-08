export default function ResearchPeerContext() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        Peer Financial Context
      </h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-6">
        <p>
          Peer Financial Context is the heart of Daanaa's scoring approach. It answers the
          question: "How does this organization's financial strength compare to similar
          organizations in its field?"
        </p>

        <div className="bg-soft-gold/10 rounded-lg p-4">
          <p className="font-semibold text-deep-navy mb-2">The Core Metric</p>
          <p className="text-sm">
            Peer Financial Context = percentile rank of organization's revenue within its
            operating model + revenue band peer group.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">How It Works</h3>
          <ol className="list-decimal pl-5 space-y-3">
            <li>
              <strong>Identify the peer group:</strong> Find all organizations with the same
              operating model and revenue band.
            </li>
            <li>
              <strong>Calculate position:</strong> Rank the organization by total revenue
              within that peer group.
            </li>
            <li>
              <strong>Express as percentile:</strong> If an org is in the 75th percentile, it
              has stronger revenue than 75% of its peers.
            </li>
          </ol>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">What This Means</h3>
          <div className="space-y-3">
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">High peer percentile (75+)</p>
              <p className="text-sm">Organization has strong revenue relative to peers.</p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Medium peer percentile (50-74)</p>
              <p className="text-sm">Organization is comparable to peer median.</p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Lower peer percentile (&lt;50)</p>
              <p className="text-sm">Organization is smaller than peer median.</p>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-deep-navy mb-2">⚠️ Important caveat</p>
          <p className="text-sm">
            Peer Financial Context measures financial scale, not impact, sustainability, or
            effectiveness. A 20th percentile organization may deliver superior value per
            dollar spent. Daanaa provides context, not judgment.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Why This Matters</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Fair comparison:</strong> A $100K youth program is "Large" in a rural
              model; the same amount is "Tiny" in an urban food bank model.
            </li>
            <li>
              <strong>Transparency:</strong> All peer grouping rules are public and
              explainable—no black-box algorithms.
            </li>
            <li>
              <strong>Stability:</strong> Percentile rankings are less volatile than absolute
              scores, enabling year-over-year comparison.
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
