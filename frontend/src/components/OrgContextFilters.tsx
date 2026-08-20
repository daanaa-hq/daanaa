/**
 * OrgContextFilters — Stub for Phase 3B
 *
 * Will provide discovery filters for the three key dimensions:
 * 1. Mission / Cause (NTEE category, tags)
 * 2. Geographic Reach (service states, regions)
 * 3. Financial Health (reserve level, program efficiency)
 *
 * This component is scaffolded but not yet wired. Phase 3C (current) focuses on
 * visible profile display via WhyThisMatches. Phase 3B will add search/directory
 * filtering using the same three dimensions.
 */

import { useState } from 'react'

interface OrgContextFiltersProps {
  onMissionChange?: (cause: string | null) => void
  onGeographyChange?: (states: string[]) => void
  onFinancialChange?: (band: string | null) => void
}

export default function OrgContextFilters({
  onMissionChange,
  onGeographyChange,
  onFinancialChange
}: OrgContextFiltersProps) {
  // Phase 3B: to be implemented
  // For now, return null (no filters rendered)
  return null

  /*
  const [selectedCause, setSelectedCause] = useState<string | null>(null)
  const [selectedStates, setSelectedStates] = useState<string[]>([])
  const [selectedBand, setSelectedBand] = useState<string | null>(null)

  return (
    <div className="border border-light-grey rounded-lg p-4 bg-white mb-6">
      <h3 className="font-body text-small font-semibold text-deep-navy mb-4">Filter by</h3>

      {/* Mission / Cause Filter * /}
      <div className="mb-4">
        <label className="font-body text-small text-cool-grey block mb-2">Mission</label>
        {/* TODO: populate from NTEE codes * /}
      </div>

      {/* Geographic Filter * /}
      <div className="mb-4">
        <label className="font-body text-small text-cool-grey block mb-2">Service Area</label>
        {/* TODO: multi-select states * /}
      </div>

      {/* Financial Filter * /}
      <div className="mb-4">
        <label className="font-body text-small text-cool-grey block mb-2">Financial Health</label>
        {/* TODO: radios for Strong/Stable/Emerging/Needs Support * /}
      </div>
    </div>
  )
  */
}
