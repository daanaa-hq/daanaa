export default function ResearchPeerContext() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        Peer Financial Context
      </h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-6">
        <p>
          Peer Financial Context is the heart of Daanaa's scoring approach. It answers a
          narrower question than "is this a good nonprofit": how specific a comparison can we
          honestly make between this organization and similar ones, given what's on the public
          record?
        </p>

        <div className="bg-soft-gold/10 rounded-lg p-4">
          <p className="font-semibold text-deep-navy mb-2">The Core Idea</p>
          <p className="text-sm">
            Every organization is placed into one of four context tiers. The tier says how
            specific its peer group is, not how the organization is doing. Daanaa does not
            compute a percentile ranking within these tiers.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">How It Works</h3>
          <ol className="list-decimal pl-5 space-y-3">
            <li>
              <strong>Start narrow:</strong> Try to find organizations doing the same kind of
              work, at a similar revenue size, in the same region. If there are enough of them
              with reserves data, this is Full Context, the most specific comparison we make.
            </li>
            <li>
              <strong>Widen when the group is too small:</strong> A peer group of a handful of
              organizations doesn't produce a meaningful comparison. When that happens, the
              group widens one step at a time: drop region and compare nationally instead
              (Regional Context), then drop revenue band too (Broad Category). If the record
              still can't support a comparison, we describe the kind of work without one at all
              (Archetype Only). This means almost every organization gets placed into a tier,
              just not always the same level of specificity.
            </li>
            <li>
              <strong>Show the underlying numbers:</strong> Months of operating reserves
              (unrestricted net assets divided by average monthly expenses) and program spending
              percentage, both from the organization's most recent Form 990 filing, are shown as
              reference points, not as a ranking.
            </li>
          </ol>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-deep-navy mb-2">⚠️ Important caveat</p>
          <p className="text-sm">
            A context tier measures how specific the comparison is, not impact, program quality,
            or effectiveness, and it isn't a percentile ranking. An organization in Archetype
            Only, with no peer comparison at all, may do excellent work; the record just doesn't
            yet support comparing it to similar organizations. Daanaa provides context, not
            judgment.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Why This Matters</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Fair comparison:</strong> A $100K community food bank has a different
              sustainability profile than a $100K fee-for-service organization in a different
              region. Peer groups account for the kind of work, the size, and the place, when
              the data supports it.
            </li>
            <li>
              <strong>Near-universal placement:</strong> Because the comparison widens
              automatically when a narrow group is too small, small and data-light
              organizations still get placed in a context tier instead of being left out.
              Three of the four tiers include an actual peer comparison.
            </li>
            <li>
              <strong>Transparency:</strong> All peer grouping rules are public and
              explainable, no black-box algorithms.
            </li>
            <li>
              <strong>No manufactured precision:</strong> When the public record can't support a
              tight comparison, we say so (Archetype Only) instead of forcing a number that
              would look precise but isn't backed by real peer data.
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
