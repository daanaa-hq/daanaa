// AnswerCard: the org page's above-the-fold financial-status card.
// Owns the branching this page needs to answer "legit? deductible? healthy?"
// in 10 seconds, for every org -- including the ~82% with no financial score
// and the ones the IRS has revoked. Extracted 2026-07-10 eng review (finding
// 2A) out of OrganizationDetail.tsx, which was already 1,631 lines.
//
//   render(org)
//     |
//     +-- revoked?  (org_status==='revoked' || irs_revoked===1)
//     |     -> RevokedBanner: factual, no shame language, no donate actions
//     |
//     +-- has v5 score?  (v5_context?.score?.health_signal present)
//     |     -> HealthChips: percentile + program-expense + health signal
//     |        (HEALTHY -> "Financially steady", STABLE -> "Managing well",
//     |         CAUTION -> "Could use community support" -- never the word
//     |         CAUTION itself, per research-copy-voice rule)
//     |
//     +-- else (the majority case, ~82% of public orgs)
//           -> NoDataBanner: standing + longevity + place (the "dignity
//              layer" -- what every org has even with zero filings)
import type { ApiOrganization } from '../data/api'

interface AnswerCardProps {
  org: ApiOrganization
}

const HEALTH_COPY: Record<string, { label: string; chipClass: string; textClass: string }> = {
  HEALTHY: { label: 'Financially steady', chipClass: 'bg-emerald-500/15 border-emerald-500/25', textClass: 'text-emerald-300' },
  STABLE: { label: 'Managing well', chipClass: 'bg-blue-500/10 border-blue-500/20', textClass: 'text-blue-300' },
  CAUTION: { label: 'Could use community support', chipClass: 'bg-alert-amber/50/10 border-amber-500/20', textClass: 'text-amber-300' },
}

function isRevoked(org: ApiOrganization): boolean {
  return org.org_status === 'revoked' || org.irs_revoked === 1
}

function rulingYear(ruling_date: string | null): string | null {
  if (!ruling_date) return null
  const year = ruling_date.slice(0, 4)
  return /^\d{4}$/.test(year) ? year : null
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

function HealthChips({ org }: { org: ApiOrganization }) {
  const score = org.v5_context?.score
  const signal = score?.health_signal ? HEALTH_COPY[score.health_signal] : null
  return (
    <div className="mt-6 space-y-4">
      <div className="flex flex-wrap gap-3">
        {org.program_expense_pct != null && org.program_expense_pct > 0 && (
          <div className="flex flex-col items-center gap-0.5 px-5 py-3 rounded-xl bg-white/8 border border-white/12 min-w-[110px]">
            <span className="font-display text-headline text-warm-cream leading-none">
              {org.program_expense_pct.toFixed(0)}¢
            </span>
            <span className="font-body text-label text-muted-cream text-center mt-1">per dollar to programs</span>
          </div>
        )}
        {signal && score?.percentile != null && (
          <div className="flex flex-col items-center gap-0.5 px-5 py-3 rounded-xl bg-white/8 border border-white/12 min-w-[110px]">
            <span className="font-display text-headline text-warm-cream leading-none">
              Top {Math.max(1, 100 - score.percentile)}%
            </span>
            <span className="font-body text-label text-muted-cream text-center mt-1">of peer nonprofits</span>
          </div>
        )}
        {signal && (
          <div className={`flex flex-col items-center gap-0.5 px-5 py-3 rounded-xl border min-w-[130px] ${signal.chipClass}`}>
            <span className={`font-body text-small font-semibold leading-none ${signal.textClass}`}>
              {signal.label}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function NoDataBanner({ org }: { org: ApiOrganization }) {
  const year = rulingYear(org.ruling_date)
  return (
    <div className="mt-4 flex items-start gap-3 px-4 py-3 rounded-xl bg-white/8 border border-white/12">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
        <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <p className="font-body text-small text-muted-cream leading-[1.55]">
        This organization is a registered 501(c)(3) and donations are tax-deductible.
        We don't have enough public financial detail to add context yet — that's common
        for smaller and local organizations.
        {year && ` Doing the work since ${year}.`}
      </p>
    </div>
  )
}

export default function AnswerCard({ org }: AnswerCardProps) {
  if (isRevoked(org)) return <RevokedBanner org={org} />
  if (org.v5_context?.score?.health_signal) return <HealthChips org={org} />
  return <NoDataBanner org={org} />
}
