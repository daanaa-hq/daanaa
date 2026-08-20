import { useEffect, useMemo } from 'react'
import { ApiOrganization } from '../data/api'
import { trackWhyMatchesVisible } from '../utils/analytics'
import { nonprofitSizeLabel } from '../utils/orgSize'

/**
 * WhyThisMatches — Small Org Clarity Phase 3C
 *
 * Shows 3 curated facts about why an organization matches a donor's giving:
 * 1. Mission & Impact (from mission + IRS program narrative)
 * 2. Geographic Reach (from service_scope + extracted states)
 * 3. Financial Health (reserves, program efficiency, trend)
 *
 * Measurement (Phase 3B.3):
 * - Tracks visibility: whyMatches:visible (location=org_detail, org_size_bucket)
 *
 * Stewardship alignment:
 * - P3 (evidence-based): every fact is sourced + verified
 * - P4 (small org fairness): visible, non-burying placement; no size penalty
 * - P5/P6 (transparency): neutral language, no shame framing
 *
 * Research backing: Perroni et al. (salience predicts donations); Nielsen Norman (visible > collapsed)
 */
interface FactCard {
  label: string
  content: string
  source: string
  icon?: string
}

function extractMissionFact(org: ApiOrganization): FactCard | null {
  if (!org.mission) return null

  // Prefer IRS 990 program narrative if available
  const hasIRSProgram = org.irs_program_narrative && org.irs_program_narrative.length > 0
  const source = hasIRSProgram
    ? `From their ${org.irs_program_narrative![0].year} Form 990 filing`
    : org.mission_attribution?.source_explanation || 'From their mission statement'

  return {
    label: 'Mission & Impact',
    content: org.mission.length > 200 ? org.mission.substring(0, 200) + '…' : org.mission,
    source,
    icon: '🎯'
  }
}

function extractGeographicFact(org: ApiOrganization): FactCard | null {
  const serviceStates = org.service_scope?.service_states || []
  const primaryState = org.STATE

  if (!primaryState && serviceStates.length === 0) return null

  // Always show primary state if available
  if (primaryState) {
    const content = serviceStates.length > 0
      ? `Operates in ${primaryState} and also serves ${serviceStates.join(', ')}`
      : `Based in ${primaryState}`

    return {
      label: 'Geographic Reach',
      content,
      source: 'From IRS public record & website',
      icon: '📍'
    }
  }

  return null
}

function extractFinancialFact(org: ApiOrganization): FactCard | null {
  const facts: string[] = []

  // Reserves (most important signal)
  if (org.months_of_reserve !== null && org.months_of_reserve > 0) {
    const m = Math.round(org.months_of_reserve)
    if (m >= 3) {
      facts.push(`${m} months of operating reserves`)
    } else if (m > 0) {
      facts.push(`${m} months of cash reserves`)
    }
  }

  // Program efficiency
  if (org.program_expense_ratio && org.program_expense_ratio >= 65) {
    const pct = Math.round(org.program_expense_ratio)
    facts.push(`${pct}% of budget to direct programs`)
  }

  // If we only have reserves, that's enough
  if (facts.length === 0) return null

  return {
    label: 'Financial Health',
    content: facts.join('. '),
    source: 'From IRS Form 990 & historical data',
    icon: '💰'
  }
}

export default function WhyThisMatches({ org, prominent = false }: { org: ApiOrganization; prominent?: boolean }) {
  // Use revenue_band if available, else derive from total_revenue, else 'unknown'
  const orgSizeBucket = org.revenue_band || nonprofitSizeLabel(org.total_revenue) || 'unknown'

  // Track visibility when component renders (Phase 3B.3)
  useEffect(() => {
    trackWhyMatchesVisible('org_detail', orgSizeBucket)
  }, [org.EIN, orgSizeBucket])

  const facts = useMemo(() => {
    const collected: FactCard[] = []

    const mission = extractMissionFact(org)
    if (mission) collected.push(mission)

    const geographic = extractGeographicFact(org)
    if (geographic) collected.push(geographic)

    const financial = extractFinancialFact(org)
    if (financial) collected.push(financial)

    return collected
  }, [org])

  if (facts.length === 0) {
    return null
  }

  const containerClass = prominent
    ? 'bg-gradient-to-br from-soft-gold/12 to-soft-gold/6 border border-soft-gold/30 p-8 rounded-lg mb-8'
    : 'bg-gradient-to-br from-soft-gold/10 to-soft-gold/4 border border-soft-gold/20 p-6 rounded-lg mb-8'

  const titleClass = prominent
    ? 'font-display text-title-lg text-deep-navy mb-2'
    : 'font-display text-title-sm text-deep-navy mb-2'

  return (
    <div className={containerClass}>
      <h2 className={titleClass}>Why this organization may match your giving</h2>
      <p className="font-body text-small text-cool-grey mb-6">Three key facts, with sources.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {facts.map((fact, idx) => (
          <div key={idx} className="bg-white rounded-md border border-light-grey p-4">
            <div className="flex gap-2 items-start mb-2">
              {fact.icon && <span className="text-lg flex-shrink-0">{fact.icon}</span>}
              <h3 className="font-body text-small font-semibold text-deep-navy">
                {fact.label}
              </h3>
            </div>
            <p className="font-body text-small text-deep-navy leading-relaxed mb-3">{fact.content}</p>
            <p className="font-body text-caption text-cool-grey italic">{fact.source}</p>
          </div>
        ))}
      </div>

      <div className="bg-soft-gold/8 border-l-2 border-soft-gold px-4 py-3 rounded-sm">
        <p className="font-body text-caption text-deep-navy">
          <strong>How we picked these three:</strong> We selected facts relevant to your giving and distinct from
          their mission statement alone. All sources are verified public data. If data isn't available, we say "not
          reported"—never as a negative indicator.
        </p>
      </div>
    </div>
  )
}
