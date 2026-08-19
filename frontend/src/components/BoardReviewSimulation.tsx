import React from 'react'
import type { ApiOrganization } from '../data/api'
import { getReconciledExpenseAllocation } from '../utils/expenseAllocation'

/**
 * BoardReviewSimulation component
 * 
 * Stewardship Principle #9: Decisions should be explainable
 * This component simulates how a nonprofit board or funder would perceive
 * this organization based on financial data. It's a neutral evidence-based
 * assessment, NOT a score or ranking.
 * 
 * P3: Trust signals must be evidence-based
 * P4: Small organizations treated fairly (no size bias)
 * P5: No weaponized transparency / shame framing
 */

interface BoardAssessment {
  strengths: string[]
  concerns: string[]
  confidence: 'HIGH' | 'MODERATE' | 'LOW'
  reason: string
}

function generateBoardAssessment(org: ApiOrganization): BoardAssessment {
  const strengths: string[] = []
  const concerns: string[] = []
  let dataPoints = 0
  
  // Strength: Good financial reserves
  if (org.months_of_reserve !== null && org.months_of_reserve >= 6) {
    strengths.push(`${Math.round(org.months_of_reserve)} months of financial reserves. A strong cushion for stability.`)
    dataPoints++
  }

  // Concern: Low reserves
  if (org.months_of_reserve !== null && org.months_of_reserve > 0 && org.months_of_reserve < 3) {
    concerns.push(`Only ${Math.round(org.months_of_reserve)} months of reserves. Limited financial cushion for unexpected changes.`)
    dataPoints++
  }

  // Concern: Negative net assets
  if (org.months_of_reserve !== null && org.months_of_reserve < 0) {
    concerns.push('Operating with negative net assets. A structural financial challenge.')
    dataPoints++
  }

  // Strength/concern: program spend. Data-integrity guard shared with
  // HowToHelp.tsx (utils/expenseAllocation.ts) -- this used to read raw
  // org.program_expense_pct directly, the same unguarded-field bug class
  // as the 2026-08-16 incident (found via Codex review 2026-08-19).
  const { reconciles, programPct } = getReconciledExpenseAllocation(org)
  if (reconciles && programPct !== null && programPct >= 75) {
    strengths.push(`${programPct}% of budget goes to programs. Mission-focused spending.`)
    dataPoints++
  }
  if (reconciles && programPct !== null && programPct < 50) {
    concerns.push(`Only ${programPct}% of budget goes to programs. High overhead.`)
    dataPoints++
  }

  // Strength: Solid board
  if (org.board_size !== undefined && org.board_size !== null && org.board_size >= 5) {
    strengths.push(`Board of ${org.board_size} members. Governance structure in place.`)
    dataPoints++
  }

  // Strength: Staff present
  if (org.employee_count !== undefined && org.employee_count !== null && org.employee_count > 0) {
    strengths.push(`${org.employee_count} full-time ${org.employee_count === 1 ? 'employee' : 'employees'}. Organized operations.`)
    dataPoints++
  }
  
  let confidence: 'HIGH' | 'MODERATE' | 'LOW' = 'LOW'
  if (dataPoints >= 5) confidence = 'HIGH'
  else if (dataPoints >= 3) confidence = 'MODERATE'
  
  const reason = dataPoints === 0
    ? 'Limited financial data available for assessment'
    : `${dataPoints} financial indicators available for review`
  
  return { strengths, concerns, confidence, reason }
}

export default function BoardReviewSimulation({ org }: { org: ApiOrganization }) {
  const assessment = generateBoardAssessment(org)
  
  if (assessment.strengths.length === 0 && assessment.concerns.length === 0) {
    return null // No data to show
  }
  
  const verdict = assessment.strengths.length > assessment.concerns.length
    ? 'This organization would likely be viewed favorably by a board review.'
    : assessment.concerns.length > assessment.strengths.length
    ? 'This organization faces some financial challenges that a board would want to monitor.'
    : 'This organization has a mixed financial profile worth further discussion.'
  
  return (
    <details className="mt-6 group">
      <summary className="cursor-pointer text-soft-gold hover:text-bright-gold font-medium flex items-center gap-2">
        <span>Board review assessment</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="group-open:rotate-180 transition-transform">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </summary>
      
      <div className="mt-4 p-4 bg-soft-gold/5 border border-soft-gold/20 rounded-lg space-y-4">
        {/* Verdict */}
        <p className="font-body text-small text-deep-navy font-medium">{verdict}</p>
        
        {/* Strengths */}
        {assessment.strengths.length > 0 && (
          <div>
            <p className="font-body text-label text-deep-gold font-semibold mb-2">Strengths</p>
            <ul className="space-y-1">
              {assessment.strengths.map((s, i) => (
                <li key={i} className="font-body text-small text-deep-navy flex gap-2">
                  <span className="text-success-green flex-shrink-0">✓</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Concerns */}
        {assessment.concerns.length > 0 && (
          <div>
            <p className="font-body text-label text-deep-gold font-semibold mb-2">Areas to monitor</p>
            <ul className="space-y-1">
              {assessment.concerns.map((c, i) => (
                <li key={i} className="font-body text-small text-deep-navy flex gap-2">
                  <span className="text-alert-amber flex-shrink-0">⚠</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Confidence */}
        <div className="pt-2 border-t border-soft-gold/20">
          <p className="font-body text-caption text-cool-grey">
            Confidence: <strong>{assessment.confidence}</strong> ({assessment.reason})
          </p>
        </div>
      </div>
    </details>
  )
}
