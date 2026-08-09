import { Link } from 'react-router-dom'
export default function ResearchMethodology() {
  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-6">V6 technical notes</h2>

      <div className="prose prose-sm max-w-none text-cool-grey space-y-6">
        <p>
          The public explanation lives on the Methodology page. This section records the technical choices behind V6 for advisors, researchers, and nonprofit practitioners. The aim is useful context without turning peer patterns into ratings.
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
            V6 context is traceable and versioned
          </p>
          <p className="text-sm">
            Organization-reported data, peer reference data, and AI-assisted summaries are kept separate. AI-assisted summaries do not determine peer groups or financial context.
          </p>
        </div>
        <p className="text-sm"><Link to="/methodology" className="font-semibold text-soft-gold hover:text-bright-gold">Read the plain-language methodology →</Link></p>

        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Key Concepts</h3>
          <dl className="space-y-4">
            <div>
              <dt className="font-semibold text-deep-navy">Funding pattern</dt>
              <dd className="text-sm mt-1">
                The available funding pattern is one input to a comparable peer group. It may be reported or inferred, and it never stands in for the organization's own explanation of its work.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Scale and revenue</dt>
              <dd className="text-sm mt-1">
                Revenue is used when available to avoid comparing organizations of very different scale. When it is missing, we do not invent it and may show broader or descriptive context.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Peer Group</dt>
              <dd className="text-sm mt-1">
                A peer group uses the available category, geography, scale, and funding pattern. The page shows the group and source years so donors can understand what the comparison does and does not say.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Peer financial context</dt>
              <dd className="text-sm mt-1">
                We show direct financial information when it is available. When it is not, we may show typical patterns among similar organizations. Inferred context never claims to describe the organization’s actual finances. It is context for donors, not a verdict on mission quality.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Confidence and limits</dt>
              <dd className="text-sm mt-1">
                Confidence describes the strength of the available evidence and the size of the comparison group. It does not describe the organization’s worth, effectiveness, or need for support.
              </dd>
            </div>
            <div>
              <dt className="font-semibold text-deep-navy">Data Completeness</dt>
              <dd className="text-sm mt-1">
                Organizations have varying levels of public data available: some file complete 990s
                with detailed financials, others are smaller and file simpler returns, and some are
                newly formed or have incomplete records. This affects which metrics we can calculate
                and how confident we are in the context we provide. Financial context and data
                availability are independent. A complete dataset does not indicate better performance.
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
