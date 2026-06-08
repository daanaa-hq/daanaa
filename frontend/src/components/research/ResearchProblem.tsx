export default function ResearchProblem() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">
        The Discovery Problem
      </h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-6">
        <p>
          Philanthropy has a visibility problem. Donors, foundations, and community leaders
          easily find the household-name nonprofits—the 3% with major endowments, foundation
          backing, or national profiles.
        </p>

        <div className="bg-warm-cream border-l-4 border-soft-gold p-4">
          <p className="font-semibold text-deep-navy mb-2">The statistics:</p>
          <p>
            97% of nonprofits have revenue under $5M. Most do hyper-local work: food banks
            in rural counties, literacy programs in underserved neighborhoods, legal aid for
            immigrant families. Their work is invisible to most donors because they lack the
            resources for national marketing or foundation relationships.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Why this matters</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>
              <strong>Donor impact is misaligned with need:</strong> Billions flow to
              well-known organizations while local crises go underfunded.
            </li>
            <li>
              <strong>Hidden gems are missed:</strong> High-impact small organizations
              struggle to grow because they're simply not discoverable.
            </li>
            <li>
              <strong>Communities lose out:</strong> Local fundraisers, workplace giving
              programs, and community foundations lack discovery tools.
            </li>
          </ul>
        </div>

        <p>
          Daanaa exists to solve this. We surface the invisible 97% and provide transparent,
          peer-based context to help donors, advisors, and communities make informed
          giving decisions.
        </p>
      </div>
    </div>
  )
}
