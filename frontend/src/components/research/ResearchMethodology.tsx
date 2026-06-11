export default function ResearchMethodology() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">Our Methodology</h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-6">
        <p>
          Daanaa's approach is built on three pillars: public data, peer context, and
          radical transparency. We don't predict impact—we provide the financial and
          operational context donors need to evaluate fit.
        </p>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Data Sources</h3>
          <ul className="space-y-3">
            <li>
              <strong className="text-deep-navy">IRS Form 990:</strong> Official nonprofit
              tax returns filed annually, the legal source of truth for U.S. nonprofits.
            </li>
            <li>
              <strong className="text-deep-navy">IRS Business Master File:</strong> Real-time
              nonprofit registration and status data.
            </li>
            <li>
              <strong className="text-deep-navy">ProPublica Nonprofit Explorer:</strong>{' '}
              Historical 990 data, searchable and verifiable.
            </li>
            <li>
              <strong className="text-deep-navy">Organization websites:</strong> Mission
              statements, leadership, and official websites verified via direct outreach.
            </li>
          </ul>
        </div>

        <div className="bg-soft-gold/10 rounded-lg p-4">
          <p className="text-sm font-semibold text-deep-navy mb-2">
            🔒 We never use proprietary scoring models or machine learning predictions
          </p>
          <p className="text-sm">
            All findings are traceable to public records and explicit calculation rules.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Key Concepts</h3>
          <dl className="space-y-4">
            <div>
              <dt className="font-semibold text-deep-navy">Operating Model</dt>
              <dd className="text-sm mt-1">
                How an organization delivers its mission: Direct Service, Activity
                Programming, Advocacy & Research, Faith Community, etc. (9 models total)
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Revenue Band</dt>
              <dd className="text-sm mt-1">
                Operating model–specific revenue brackets. A $200K food bank is "Large" in
                its model; a $200K health clinic is "Nano." This prevents unfair comparison.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Peer Financial Context</dt>
              <dd className="text-sm mt-1">
                The organization's revenue percentile rank within its operating model +
                revenue band peer group. Contextual, not absolute.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Lamp Tier</dt>
              <dd className="text-sm mt-1">
                A visibility indicator (Beacon, Torch, Candle, Spark) based on data
                completeness, not organizational quality.
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
