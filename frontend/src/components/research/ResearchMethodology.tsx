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
              <strong className="text-deep-navy">Organization websites:</strong> Official
              websites verified programmatically and cross-referenced against IRS records.
            </li>
          </ul>
        </div>

        <div className="bg-soft-gold/10 rounded-lg p-4">
          <p className="text-sm font-semibold text-deep-navy mb-2">
            🔒 Financial scores derive solely from public IRS data
          </p>
          <p className="text-sm">
            All peer context scores and health signals are deterministic: traceable to
            public Form 990 filings and explicit calculation rules, with no black-box
            algorithms or paid data providers. Mission summaries and cause tags are generated
            by a local AI model and are labeled accordingly — they do not affect scores.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Key Concepts</h3>
          <dl className="space-y-4">
            <div>
              <dt className="font-semibold text-deep-navy">Financial Archetype</dt>
              <dd className="text-sm mt-1">
                How an organization funds itself: Donation-Funded Programs (community
                fundraising), Fee-for-Service Operators (earned revenue), or Endowment-Funded
                Grantmakers (reserve-driven). Archetype shapes financial strategy and
                sustainability drivers.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Revenue Band</dt>
              <dd className="text-sm mt-1">
                Three universal bands applied across all archetypes: Micro (&lt;$150K),
                Professional ($150K–$700K), Established (&gt;$700K). Bands prevent unfair
                comparison between a $100K startup and a $50M institution.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Peer Group</dt>
              <dd className="text-sm mt-1">
                A peer group is formed by combining archetype + revenue band. An organization is
                benchmarked only against others in its peer group. Each peer group has its own
                typical financial profile.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Financial Context Score</dt>
              <dd className="text-sm mt-1">
                A 0–100 percentile rank within the peer group, based on months of operating
                reserves. A score of 75 means the organization holds more reserves than 75% of
                its peers. This is context, not a verdict. A lower score often means an
                organization needs more community support — not that it is doing less good.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Health Signal</dt>
              <dd className="text-sm mt-1">
                An independent assessment of financial context: Financially healthy (strong reserves
                and revenue stability), Financially stable (adequate resources for peers), or Needs
                support (limited reserves or revenue volatility). Not a verdict — a flag for deeper review.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Lamp Tier</dt>
              <dd className="text-sm mt-1">
                A separate visibility indicator (Beacon, Torch, Candle, Spark) based on data
                completeness, not financial performance. Visibility and financial context are
                independent dimensions.
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
