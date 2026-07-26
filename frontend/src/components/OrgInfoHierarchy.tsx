import { ReactNode } from 'react'
import type { ApiOrganization } from '../data/api'
import GiveYourWayRouter from './GiveYourWayRouter'

/**
 * OrgInfoHierarchy: Display org information from most common to least common.
 *
 * Stewardship alignment:
 * - P3 (Evidence-based): Only show data we have; disclose sources
 * - P4 (Small org fairness): Don't penalize for missing data
 * - P5 (No shame): Frame gaps as "we're learning" not "they're incomplete"
 */

interface InfoBlockProps {
  title: string
  children?: ReactNode
  isMissing?: boolean
  missingReason?: string
}

function InfoBlock({ title, children, isMissing = false, missingReason }: InfoBlockProps) {
  return (
    <div className="mb-6 pb-6 border-b border-soft-grey last:border-b-0">
      <h3 className="text-sm font-semibold text-navy-dark mb-3">{title}</h3>
      {isMissing ? (
        <div className="p-3 bg-soft-gold/10 rounded-lg border border-soft-gold/30">
          <p className="text-sm text-navy-mid">
            {missingReason || "We're still learning about this org. Help us by verifying their information."}
          </p>
        </div>
      ) : (
        <div>{children}</div>
      )}
    </div>
  )
}

interface OrgInfoHierarchyProps {
  org: ApiOrganization
}

export default function OrgInfoHierarchy({ org }: OrgInfoHierarchyProps) {
  // Determine data availability score for each field
  const dataAvailable = {
    mission: !!org.mission,
    donate: org.donate_url_status === 'beta' || org.donate_url_status === 'claimed',
    website: org.website_status === 'ok',
    financial: !!org.merit_score,
    board: !!org.board_size,
    leadership: false, // not in current ApiOrganization schema
    programs: false, // not in current ApiOrganization schema
  }

  return (
    <div className="space-y-6">
      {/* TIER 1: Mission (95%+ have) */}
      {dataAvailable.mission ? (
        <InfoBlock title="Mission" >
          <p className="text-sm leading-relaxed text-navy-mid">{org.mission}</p>
          {org.mission_source && (
            <p className="text-xs text-cool-grey mt-2">
              Source: {org.mission_source === 'irs_990' ? 'IRS Form 990'
                : org.mission_source === 'ai_ntee' ? 'NTEE category'
                : org.mission_source === 'ai_web_grounded' ? 'Organization website'
                : org.mission_source === 'claimed' ? 'Verified by organization'
                : 'Public sources'}
            </p>
          )}
        </InfoBlock>
      ) : (
        <InfoBlock
          title="Mission"
          isMissing
          missingReason="We're still learning about this organization's mission. Help us by verifying their website or Form 990 filing."
        />
      )}

      {/* TIER 2: Financial Context (97%+ with v6) */}
      {dataAvailable.financial ? (
        <InfoBlock title="Financial Context">
          <div className="text-sm text-navy-mid space-y-2">
            {org.merit_score && (
              <p>Financial health ranking: <strong>{Math.round(org.merit_score)}/100</strong> in their peer group</p>
            )}
            {org.merit_band && (
              <p>Organization size: <strong>{org.merit_band}</strong></p>
            )}
          </div>
        </InfoBlock>
      ) : (
        <InfoBlock
          title="Financial Context"
          isMissing
          missingReason="This is a very small organization or newly formed. Financial data may become available when they file their next Form 990."
        />
      )}

      {/* TIER 3: ALWAYS show ways to give */}
      <InfoBlock title="How to Give">
        <div className="space-y-4">
          {/* Leverage existing GiveYourWayRouter component */}
          <GiveYourWayRouter
            ein={org.EIN}
            organizationName={org.organization_name}
            streetAddress={org.street_address}
            donateUrl={org.donate_url}
            donateUrlStatus={org.donate_url_status}
            website={org.website}
            websiteStatus={org.website_status}
          />

          {/* Meta: Help us improve */}
          <div className="p-3 bg-soft-gold/10 border border-soft-gold/30 rounded-lg">
            <p className="text-xs text-navy-mid">
              <strong>Help us help you:</strong> If you know their donation process, <a href="#mistake-registry" className="text-warm-red hover:underline">tell us here</a> so we can verify it for others.
            </p>
          </div>
        </div>
      </InfoBlock>

      {/* TIER 4: Website (70%+) */}
      {dataAvailable.website && org.website && (
        <InfoBlock title="Learn More">
          <a
            href={org.website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-warm-red hover:underline text-sm"
          >
            {org.website} →
          </a>
        </InfoBlock>
      )}

      {/* TIER 5: Board/Governance (40%+) */}
      {dataAvailable.board ? (
        <InfoBlock title="Governance">
          <div className="text-sm text-navy-mid space-y-2">
            {org.board_size && (
              <p>Board size: <strong>{org.board_size} members</strong></p>
            )}
          </div>
        </InfoBlock>
      ) : (
        <InfoBlock
          title="Governance"
          isMissing
          missingReason="Board and leadership information comes from recent Form 990 filings. It will appear here once available."
        />
      )}

      {/* ALWAYS SHOW: Trust Note */}
      <div className="mt-8 p-4 bg-navy-dark/5 rounded-lg border border-navy-dark/10">
        <p className="text-xs text-navy-mid leading-relaxed">
          <strong>We believe in transparency:</strong> Missing information doesn't mean this organization is incomplete—it means we're still learning. Small and young organizations may not have filed recent tax returns yet. We're committed to showing you what we know, being honest about what we don't, and helping small orgs get better visibility.
        </p>
      </div>
    </div>
  )
}
