import { ReactNode } from 'react'
import type { ApiOrganization } from '../data/api'
import GiveYourWayRouter from './GiveYourWayRouter'
import { normalizeExternalUrl } from '../utils/externalLink'
import { nonprofitSizeLabel } from '../utils/orgSize'
import { taxDeductibleToStatus } from '../utils/taxDeductible'

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
    donate: org.donate_url_status === 'beta' || org.donate_url_status === 'claimed',
    // Match the app's established rule (utils/actionRow.ts), not a stricter local
    // one: show a website when it verified ok/beta, OR when we hold a URL we simply
    // have not checked yet (status null). The old `=== 'ok'` gate hid real websites
    // -- e.g. Harvard carries www.harvard.edu with status 'no_website_found' -- which
    // is a coverage gap on our side, not evidence the org has no site (P4/P5).
    website: org.website_status === 'ok' || org.website_status === 'beta'
      || (!!org.website && org.website_status == null),
    financial: !!org.merit_score,
    board: !!org.board_size,
    leadership: false, // not in current ApiOrganization schema
    programs: false, // not in current ApiOrganization schema
  }

  return (
    <div className="space-y-6">
      {/* Mission removed from this tier 2026-08-08: it duplicated the hero's
          mission paragraph verbatim (OrganizationDetail.tsx renders org.mission
          directly under the org name). Source attribution / AI-generated
          disclosure the hero doesn't yet carry is TODO'd separately rather
          than kept here as a reason to duplicate the whole paragraph. */}

      {/* TIER 2: Financial Context (97%+ with v6) */}
      {dataAvailable.financial ? (
        <InfoBlock title="Financial Context">
          <div className="text-sm text-navy-mid space-y-2">
            {/* Peer context and health signal shown via V5Context + FinancialContext
                components on the main detail page — no ranking here (Principle #7). */}
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
      <div id="ways-to-give" className="scroll-mt-24">
        <InfoBlock title="Ways to Give">
          {/* Removed 2026-08-08: this warned "not fully verified" whenever our own
              data lacked a Pub 78 signal, which read to donors as doubt about the
              nonprofit rather than a gap in our coverage. Every org listed here is
              IRS deductibility code 1 and absent from the daily Auto-Revocation
              sync, so the honest presentation is the positive statement below. */}
          {org.tax_deductible === false && (
            <p className="text-sm text-navy-mid bg-soft-gold/10 border border-soft-gold/30 rounded-lg p-3 mb-4">
              Confirm this organization's current status with the IRS before giving.
            </p>
          )}
        <div className="space-y-4">
          {/* Leverage existing GiveYourWayRouter component */}
          <GiveYourWayRouter
            ein={org.EIN}
            organizationName={org.organization_name}
            streetAddress={org.street_address}
            city={org.CITY}
            state={org.STATE}
            zipcode={org.zipcode}
            donateUrl={org.donate_url}
            donateUrlStatus={org.donate_url_status}
            website={org.website}
            websiteStatus={org.website_status}
            irsEligibilityStatus={taxDeductibleToStatus(org.tax_deductible)}
          />

          {/* Meta: Help us improve */}
          <div className="p-3 bg-soft-gold/10 border border-soft-gold/30 rounded-lg">
            <p className="text-xs text-navy-mid">
              <strong>Help us help you:</strong> If you know their donation process, <a href="#mistake-registry" className="text-warm-red hover:underline">tell us here</a> so we can verify it for others.
            </p>
          </div>
        </div>
      </InfoBlock>
      </div>

      {/* TIER 4: Website (70%+) */}
      {/* normalizeExternalUrl, not the raw value (2026-08-08): stored websites are
          bare domains ("www.harvard.edu"), which a browser resolves as a RELATIVE
          path -- clicking sent visitors to /org/<ein>/www.harvard.edu instead of the
          org's site. The helper also rejects javascript:/data: schemes, so the raw
          href was an XSS vector as well as a broken link. OrgCard already used it;
          this page did not. */}
      {dataAvailable.website && normalizeExternalUrl(org.website) && (
        <InfoBlock title="Learn More">
          <a
            href={normalizeExternalUrl(org.website)!}
            target="_blank"
            rel="noopener noreferrer"
            className="text-warm-red hover:underline text-sm"
          >
            {org.website} →
          </a>
        </InfoBlock>
      )}

      {/* TIER 5: Organization Profile — size + board (40%+ coverage).
          Size derives from total_revenue, not the dormant `merit_band`
          lamp-tier field this used to read — that field is unset for most
          orgs post-retirement and was rendering as a bare "Size: 0" or
          blank. See LESSONS.md 2026-08-08. */}
      {(() => {
        const sizeLabel = nonprofitSizeLabel(org.total_revenue)
        return (dataAvailable.board || sizeLabel) ? (
        <InfoBlock title="Organization">
          <div className="text-sm text-navy-mid space-y-2">
            {sizeLabel && (
              <p>Size: <strong>{sizeLabel}</strong></p>
            )}
            {org.board_size && (
              <p>Board: <strong>{org.board_size} members</strong></p>
            )}
          </div>
        </InfoBlock>
      ) : (
        <InfoBlock
          title="Organization"
          isMissing
          missingReason="Organization and board information comes from recent Form 990 filings. It will appear here once available."
        />
        )
      })()}

      {/* ALWAYS SHOW: Trust Note */}
      <div className="mt-8 p-4 bg-navy-dark/5 rounded-lg border border-navy-dark/10">
        <p className="text-xs text-navy-mid leading-relaxed">
          <strong>We believe in transparency:</strong> Missing information doesn't mean this organization is incomplete—it means we're still learning. Small and young organizations may not have filed recent tax returns yet. We're committed to showing you what we know, being honest about what we don't, and helping small orgs get better visibility.
        </p>
      </div>
    </div>
  )
}
