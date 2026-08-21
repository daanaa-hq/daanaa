/**
 * OrgContextFilters — Phase 3B.4 Discovery Filters
 *
 * Three controlled dropdowns for refining search results:
 * 1. Mission / Cause tags (multi-select)
 * 2. Geographic Reach / Service States (multi-select)
 * 3. Financial Health / Revenue Band (single-select)
 *
 * Stewardship P4 (small org fairness): filtering by context helps small orgs
 * compete for discovery by allowing donors to refine by criteria that matter
 * (e.g., "Serves in IL" + "Micro" + "Mental health").
 *
 * UX Research: Nielsen Norman (visible filters beat hidden); Codex findings
 * (donors use cause + geography + size as decision signals).
 */

import { useState } from 'react'
import { ChevronDown, X } from 'lucide-react'

interface OrgContextFiltersProps {
  // Selected values (controlled by parent Directory)
  missionTags: string[]
  serviceStates: string[]
  revenueBand: string | null

  // Callbacks to update parent state
  onMissionChange: (tags: string[]) => void
  onGeographyChange: (states: string[]) => void
  onFinancialChange: (band: string | null) => void
}

// Curated mission tags for discovery (subset of full cause_tags vocabulary)
const MISSION_OPTIONS = [
  { value: 'Food', label: 'Food & Agriculture' },
  { value: 'Health', label: 'Health & Medical' },
  { value: 'Education', label: 'Education' },
  { value: 'Environment', label: 'Environment & Climate' },
  { value: 'Housing', label: 'Housing & Homelessness' },
  { value: 'Poverty', label: 'Poverty & Economic Dev' },
  { value: 'Arts', label: 'Arts & Culture' },
  { value: 'Community', label: 'Community Development' },
  { value: 'Youth', label: 'Youth & Children' },
  { value: 'Mental', label: 'Mental Health & Addiction' },
  { value: 'Disability', label: 'Disability Services' },
  { value: 'Veterans', label: 'Veterans & Military' },
]

// US States + territories for service area filter
const STATE_OPTIONS = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
  'DC', 'PR', 'GU', 'VI', 'AS', 'MP',
]

// Revenue bands
const REVENUE_BAND_OPTIONS = [
  { value: 'Micro', label: 'Micro (<$250K)' },
  { value: 'Small', label: 'Small ($250K–$1M)' },
  { value: 'Medium', label: 'Medium ($1M–$10M)' },
  { value: 'Large', label: 'Large ($10M–$100M)' },
  { value: 'Major', label: 'Major (>$100M)' },
]

export default function OrgContextFilters({
  missionTags,
  serviceStates,
  revenueBand,
  onMissionChange,
  onGeographyChange,
  onFinancialChange,
}: OrgContextFiltersProps) {
  const [missionOpen, setMissionOpen] = useState(false)
  const [geographyOpen, setGeographyOpen] = useState(false)
  const [financialOpen, setFinancialOpen] = useState(false)

  const toggleMissionTag = (tag: string) => {
    if (missionTags.includes(tag)) {
      onMissionChange(missionTags.filter(t => t !== tag))
    } else {
      onMissionChange([...missionTags, tag])
    }
  }

  const toggleServiceState = (state: string) => {
    if (serviceStates.includes(state)) {
      onGeographyChange(serviceStates.filter(s => s !== state))
    } else {
      onGeographyChange([...serviceStates, state])
    }
  }

  // Return null if no filters are selected (Phase 3B.4 MVP: show only when filtering)
  // Later: always show as a collapsible/expandable section
  if (missionTags.length === 0 && serviceStates.length === 0 && !revenueBand) {
    return null
  }

  return (
    <div className="border border-light-grey rounded-lg p-4 bg-white mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-body text-small font-semibold text-deep-navy">
          Refining by context
        </h3>
        <button
          onClick={() => {
            onMissionChange([])
            onGeographyChange([])
            onFinancialChange(null)
          }}
          className="text-xs font-body text-soft-gold hover:text-bright-gold"
        >
          Clear all
        </button>
      </div>

      {/* Active mission tags */}
      {missionTags.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-cool-grey font-semibold mb-2 uppercase">Mission</p>
          <div className="flex flex-wrap gap-2">
            {missionTags.map(tag => (
              <div
                key={tag}
                className="inline-flex items-center gap-2 bg-soft-gold/20 text-deep-navy px-3 py-1 rounded-full text-xs font-medium"
              >
                {MISSION_OPTIONS.find(o => o.value === tag)?.label || tag}
                <button
                  onClick={() => toggleMissionTag(tag)}
                  className="hover:text-soft-gold"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active service states */}
      {serviceStates.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-cool-grey font-semibold mb-2 uppercase">Service Area</p>
          <div className="flex flex-wrap gap-2">
            {serviceStates.map(state => (
              <div
                key={state}
                className="inline-flex items-center gap-2 bg-soft-gold/20 text-deep-navy px-3 py-1 rounded-full text-xs font-medium"
              >
                {state}
                <button
                  onClick={() => toggleServiceState(state)}
                  className="hover:text-soft-gold"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active revenue band */}
      {revenueBand && (
        <div className="mb-4">
          <p className="text-xs text-cool-grey font-semibold mb-2 uppercase">Revenue Band</p>
          <div className="inline-flex items-center gap-2 bg-soft-gold/20 text-deep-navy px-3 py-1 rounded-full text-xs font-medium">
            {REVENUE_BAND_OPTIONS.find(o => o.value === revenueBand)?.label || revenueBand}
            <button
              onClick={() => onFinancialChange(null)}
              className="hover:text-soft-gold"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      {/* Dropdown controls (hidden by default, shown when clicked) */}
      <div className="space-y-3 border-t border-light-grey pt-4">
        {/* Mission dropdown */}
        <div>
          <button
            onClick={() => setMissionOpen(!missionOpen)}
            className="flex items-center justify-between w-full px-3 py-2 border border-light-grey rounded-md hover:bg-light-cream transition-colors"
          >
            <span className="text-small text-deep-navy font-medium">+ Add mission</span>
            <ChevronDown className={`w-4 h-4 text-cool-grey transition-transform ${missionOpen ? 'rotate-180' : ''}`} />
          </button>
          {missionOpen && (
            <div className="absolute bg-white border border-light-grey rounded-md mt-1 z-10 shadow-md p-2 max-w-xs">
              {MISSION_OPTIONS.map(option => (
                <label key={option.value} className="flex items-center gap-2 px-3 py-2 hover:bg-light-cream cursor-pointer rounded text-small">
                  <input
                    type="checkbox"
                    checked={missionTags.includes(option.value)}
                    onChange={() => toggleMissionTag(option.value)}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-deep-navy">{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Geography dropdown */}
        <div>
          <button
            onClick={() => setGeographyOpen(!geographyOpen)}
            className="flex items-center justify-between w-full px-3 py-2 border border-light-grey rounded-md hover:bg-light-cream transition-colors"
          >
            <span className="text-small text-deep-navy font-medium">+ Add service area</span>
            <ChevronDown className={`w-4 h-4 text-cool-grey transition-transform ${geographyOpen ? 'rotate-180' : ''}`} />
          </button>
          {geographyOpen && (
            <div className="absolute bg-white border border-light-grey rounded-md mt-1 z-10 shadow-md p-2 max-w-xs max-h-64 overflow-y-auto">
              {STATE_OPTIONS.map(state => (
                <label key={state} className="flex items-center gap-2 px-3 py-2 hover:bg-light-cream cursor-pointer rounded text-small">
                  <input
                    type="checkbox"
                    checked={serviceStates.includes(state)}
                    onChange={() => toggleServiceState(state)}
                    className="w-4 h-4 rounded"
                  />
                  <span className="text-deep-navy">{state}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Financial dropdown */}
        <div>
          <button
            onClick={() => setFinancialOpen(!financialOpen)}
            className="flex items-center justify-between w-full px-3 py-2 border border-light-grey rounded-md hover:bg-light-cream transition-colors"
          >
            <span className="text-small text-deep-navy font-medium">+ Add revenue band</span>
            <ChevronDown className={`w-4 h-4 text-cool-grey transition-transform ${financialOpen ? 'rotate-180' : ''}`} />
          </button>
          {financialOpen && (
            <div className="absolute bg-white border border-light-grey rounded-md mt-1 z-10 shadow-md p-2">
              {REVENUE_BAND_OPTIONS.map(option => (
                <label key={option.value} className="flex items-center gap-2 px-3 py-2 hover:bg-light-cream cursor-pointer rounded text-small">
                  <input
                    type="radio"
                    name="revenue-band"
                    checked={revenueBand === option.value}
                    onChange={() => onFinancialChange(option.value)}
                    className="w-4 h-4"
                  />
                  <span className="text-deep-navy">{option.label}</span>
                </label>
              ))}
              {revenueBand && (
                <button
                  onClick={() => onFinancialChange(null)}
                  className="w-full text-left px-3 py-2 text-xs text-cool-grey hover:bg-light-cream rounded"
                >
                  Clear selection
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
