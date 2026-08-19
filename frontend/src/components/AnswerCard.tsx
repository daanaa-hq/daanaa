// AnswerCard: the org page's above-the-fold financial-status card.
// Owns the branching this page needs to answer "legit? deductible? healthy?"
// in 10 seconds, for every org -- including the ~82% with no financial score
// and the ones the IRS has revoked. Extracted 2026-07-10 eng review (finding
// 2A) out of OrganizationDetail.tsx, which was already 1,631 lines.
//
// This card handles basic public-record status. v6 financial context is rendered
// separately below it so every organization follows the same presentation.
import type { ApiOrganization } from '../data/api'

interface AnswerCardProps {
  org: ApiOrganization
}

function isRevoked(org: ApiOrganization): boolean {
  return org.org_status === 'revoked' || org.irs_revoked === 1
}

function RevokedBanner({ org }: { org: ApiOrganization }) {
  return (
    <div className="mt-4 flex items-start gap-3 px-4 py-3 rounded-xl bg-white/8 border border-white/12">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <div>
        <p className="font-body text-small text-muted-cream leading-[1.55]">
          IRS records show this organization's tax-exempt status was automatically revoked.
          Donations made now would not be tax-deductible.
        </p>
        <a
          href={`https://projects.propublica.org/nonprofits/organizations/${org.EIN}`}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1.5 inline-flex items-center gap-1 font-body text-caption text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2"
        >
          View the IRS record
        </a>
      </div>
    </div>
  )
}

// Consolidated 2026-08-16 and 2026-08-18: this used to also carry a
// "no financial score yet" sentence (NoDataBanner) and a "Since {year}"
// fact. The year moved to a badge in the row below (utils/badges.ts,
// 2026-08-18). The "no financial score" sentence is removed entirely as of
// 2026-08-19 (Codex review): it triggered on the exact same condition
// (!org.scoring_tier) as FinancialContext.tsx's own "Category context" box
// further down the page, which explains the same gap at greater length --
// a donor saw the identical fact twice. One surface now, not two.
//
// (HEALTH_COPY / a HealthChips-style peer-percentile display used to live
// here too but was dead code -- defined, never rendered, verified via
// grep before removal 2026-08-19.)
export default function AnswerCard({ org }: AnswerCardProps) {
  if (isRevoked(org)) return <RevokedBanner org={org} />
  return null
}
