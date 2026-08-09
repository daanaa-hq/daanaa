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
            Peer Financial Context = percentile rank of months of operating reserves within
            the organization's peer group, chosen as narrowly as the public record allows.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">How It Works</h3>
          <ol className="list-decimal pl-5 space-y-3">
            <li>
              <strong>Identify the peer group:</strong> Find organizations doing the same kind
              of work, at a similar revenue size, in the same region. This is the narrowest,
              most useful comparison, called Full Context.
            </li>
            <li>
              <strong>Widen when the group is too small:</strong> A narrow peer group of five
              organizations doesn't produce a meaningful percentile. When that happens, the
              comparison widens step by step: drop region (Regional Context), then broaden the
              category (Broad Category), and if the record still can't support a comparison,
              describe the kind of work without a percentile at all (Archetype Only). This
              means almost every organization gets a comparison, just not always the same
              level of it.
            </li>
            <li>
              <strong>Calculate reserves:</strong> Compute months of operating reserves
              (unrestricted net assets divided by average monthly expenses) from the
              organization's most recent Form 990 filing.
            </li>
            <li>
              <strong>Express as percentile:</strong> If an org is in the 75th percentile, it
              holds more reserves than 75% of its peers in that comparison group.
            </li>
          </ol>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">What This Means</h3>
          <div className="space-y-3">
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">High peer percentile (75+)</p>
              <p className="text-sm">Organization holds stronger reserves relative to peers, a financial cushion against disruption.</p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Medium peer percentile (50-74)</p>
              <p className="text-sm">Organization's reserve position is comparable to the peer median.</p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Lower peer percentile (&lt;50)</p>
              <p className="text-sm">Organization holds fewer reserves than the peer median, often because demand for its services outpaces available funding, not because its work is less valuable.</p>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-deep-navy mb-2">⚠️ Important caveat</p>
          <p className="text-sm">
            Peer Financial Context measures reserve strength relative to peers, not impact,
            program quality, or effectiveness. A 20th percentile organization may deliver
            superior value per dollar spent. Daanaa provides context, not judgment.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Why This Matters</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Fair comparison:</strong> A $100K community food bank has a different
              sustainability profile than a $100K fee-for-service organization in a different
              region. Peer groups account for the kind of work, the size, and the place.
            </li>
            <li>
              <strong>Near-universal coverage:</strong> Because the comparison widens
              automatically when a narrow group is too small, small and data-light
              organizations still get placed in a context tier instead of being left out.
            </li>
            <li>
              <strong>Transparency:</strong> All peer grouping rules are public and
              explainable, no black-box algorithms.
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
