import { useEffect, useState } from 'react'
import { loadResearchSnapshot } from '../../data/researchSnapshot'

interface ResearchDataMovementProps {
  sessionToken: string
  metadata: any
}

export default function ResearchDataMovement({
  sessionToken,
  metadata,
}: ResearchDataMovementProps) {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Trigger load of snapshot (for consistency, though we mainly use metadata)
    loadResearchSnapshot()
      .catch((error) => console.error('Failed to load snapshot:', error))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <h2 className="text-3xl font-display text-deep-navy mb-4">
          What's Changed
        </h2>
        <p className="text-sm text-cool-grey">Loading…</p>
      </div>
    )
  }

  const lastUpdate = metadata?.data_period
    ? new Date(metadata.data_period).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Unknown'

  const totalOrgs = metadata?.total_organizations || 1871724
  const revokedCount = 192889 // As of most recent sync
  const fullRegistry = totalOrgs + revokedCount

  return (
    <div>
      <h2 className="text-3xl font-display text-deep-navy mb-4">
        What's Changed
      </h2>

      <p className="text-lg text-cool-grey mb-6 max-w-2xl">
        We monitor nonprofit status data continuously. Here's what the most recent
        IRS data sync revealed—observations without conclusions. We're all learning
        how to read this data responsibly.
      </p>

      <div className="space-y-6 max-w-2xl">
        {/* Current State */}
        <div className="bg-deep-navy/[0.02] rounded-lg p-6 border border-light-grey">
          <h3 className="text-lg font-semibold text-deep-navy mb-4">Current State</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-baseline">
              <span className="text-cool-grey">
                Active, tax-deductible 501(c)(3)s in our index:
              </span>
              <span className="font-display text-2xl text-deep-navy">
                {totalOrgs.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-cool-grey">
                Revoked or otherwise removed from active status:
              </span>
              <span className="font-display text-2xl text-deep-navy">
                {revokedCount.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-cool-grey text-sm">
                (Full registry, including inactive: {fullRegistry.toLocaleString()})
              </span>
            </div>
          </div>
        </div>

        {/* Data Freshness */}
        <div className="bg-soft-gold/10 rounded-lg p-6 border border-soft-gold/30">
          <h3 className="text-lg font-semibold text-deep-navy mb-3">Data Freshness</h3>
          <p className="text-cool-grey mb-4">
            Our last sync with IRS data occurred on <strong>{lastUpdate}</strong>. The
            active nonprofit census is updated daily by the IRS Business Master File,
            and we sync those updates automatically.
          </p>
          <p className="text-sm text-slate leading-relaxed">
            The 192,889 revoked organizations represent a mix of mergers, closures, and
            nonprofit status changes over time. We exclude them from our main index to
            keep our public count accurate: {totalOrgs.toLocaleString()} active
            501(c)(3)s, not 2.06M.
          </p>
        </div>

        {/* Coverage Notes */}
        <div>
          <h3 className="text-lg font-semibold text-deep-navy mb-4">
            Coverage &amp; Observations
          </h3>
          <div className="space-y-4">
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Mission statements</p>
              <p className="text-sm text-slate mt-1">
                We have curated mission information for all 1.87M active nonprofits. Some
                come directly from IRS 990 forms; others from scraped websites or AI
                analysis of their NTEE classification. All are reviewed before surfacing.
              </p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Donation links</p>
              <p className="text-sm text-slate mt-1">
                We've verified working donation URLs for {(3512).toLocaleString()} organizations (0.2% of the index). The
                rate is low because many smaller nonprofits don't have a web presence or
                use old donation systems we haven't yet identified. This is an active work
                item.
              </p>
            </div>
            <div className="border-l-4 border-soft-gold pl-4">
              <p className="font-semibold text-deep-navy">Financial context</p>
              <p className="text-sm text-slate mt-1">
                We score 411,531 organizations (22% of the index) using their recent IRS
                990 data. The other 78% lack sufficient financial disclosure to benchmark
                fairly. This isn't a judgment—many very good nonprofits fall below the
                990 filing threshold.
              </p>
            </div>
          </div>
        </div>

        {/* Learning Note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-deep-navy leading-relaxed">
            <strong>Why we show this:</strong> We believe transparency about what we know,
            what we don't, and what we're still learning makes our data more credible.
            These numbers change constantly as the IRS updates nonprofit status. If you
            notice something inconsistent with your knowledge of an organization, please
            let us know via the Correction form on that org's detail page.
          </p>
        </div>
      </div>
    </div>
  )
}
