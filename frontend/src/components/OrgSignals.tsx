import React from 'react'

interface OrgSignalsProps {
  website?: string | null
  website_status?: string | null
  mission_source?: string | null
  cause_tags?: string[] | null
  latest_tax_year?: number | null
  total_revenue?: number | null
  irs_eligibility_status?: string | null
  irs_eligibility_explanation?: string | null
}

export default function OrgSignals({
  website,
  website_status,
  mission_source,
  cause_tags,
  latest_tax_year,
  total_revenue,
  irs_eligibility_status,
  irs_eligibility_explanation,
}: OrgSignalsProps) {
  const signals: { icon: string; label: string; title: string }[] = []

  // Signal 0: IRS Tax Status (highest priority)
  if (irs_eligibility_status === 'revoked') {
    signals.push({
      icon: '⚠️',
      label: 'Revoked by IRS',
      title: irs_eligibility_explanation || 'This organization is not currently eligible for tax-deductible donations'
    })
  } else if (irs_eligibility_status === 'eligible' || irs_eligibility_status === 'verified') {
    signals.push({
      icon: '✅',
      label: 'IRS Eligible',
      title: irs_eligibility_explanation || 'IRS records indicate this organization is eligible for tax-deductible donations'
    })
  }

  // Signal 1: Website live
  if (website && website_status === 'ok') {
    signals.push({
      icon: '🌐',
      label: 'Website',
      title: 'Has a verified, live website'
    })
  }

  // Signal 2: Mission clarity
  if (mission_source && mission_source !== 'unknown') {
    const missionLabels: Record<string, string> = {
      'ai_ntee': 'Clear mission (verified)',
      'ai_web': 'Mission documented',
      'ai_generated': 'Mission described',
      'scraped': 'Mission public',
    }
    if (missionLabels[mission_source]) {
      signals.push({
        icon: '📝',
        label: 'Mission',
        title: missionLabels[mission_source]
      })
    }
  }

  // Signal 3: Financial data freshness
  if (latest_tax_year) {
    const currentYear = new Date().getFullYear()
    const yearsOld = currentYear - latest_tax_year
    if (total_revenue !== null && total_revenue !== undefined) {
      signals.push({
        icon: '💰',
        label: `${latest_tax_year} filing`,
        title: `Latest financial filing: ${latest_tax_year}`
      })
    } else if (yearsOld > 3) {
      signals.push({
        icon: '⏳',
        label: 'Limited data',
        title: `Last filing: ${latest_tax_year} (${yearsOld}+ years ago)`
      })
    }
  }

  // Signal 4: Cause tags (categorization)
  if (cause_tags && cause_tags.length > 0) {
    signals.push({
      icon: '🏷️',
      label: `${cause_tags.length} cause${cause_tags.length !== 1 ? 's' : ''}`,
      title: `Tagged: ${cause_tags.join(', ')}`
    })
  }

  if (signals.length === 0) {
    return (
      <div className="flex items-center gap-1.5 text-label text-cool-grey">
        <span className="opacity-50">Limited data · public record</span>
      </div>
    )
  }

  return (
    <ul className="flex flex-wrap gap-1.5" aria-label="Public signals">
      {signals.map((signal, idx) => (
        <li
          key={idx}
          title={signal.title}
          className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-light-grey/40 text-label text-cool-grey font-medium whitespace-nowrap"
        >
          <span aria-hidden="true">{signal.icon}</span>
          <span>{signal.label}</span>
        </li>
      ))}
    </ul>
  )
}
