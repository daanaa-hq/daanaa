/**
 * DataContextNote — Supportive explanation of data gaps for archetype-only orgs.
 * Honors Stewardship Charter #7: "Where our data is thin, we say 'we don't know
 * enough,' never 'they failed.'"
 */

import React, { useState } from 'react'
import type { ApiOrganization } from '../data/api'

interface DataContextNoteProps {
  org: ApiOrganization
  // Show note if: org has archetype but no band (no revenue data)
}

export default function DataContextNote({ org }: DataContextNoteProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Only show if archetype exists but band does NOT (archetype-only)
  const hasArchetype = org.merit_archetype_v5_label
  const hasBand = org.merit_band_v5_label

  if (!hasArchetype || hasBand) {
    return null // Don't show if we have full scoring
  }

  return (
    <div className="mt-6 p-4 rounded-lg bg-amber-50 border border-amber-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-start justify-between text-left hover:opacity-75 transition-opacity"
      >
        <div className="flex items-start gap-3 flex-1">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-amber-700 flex-shrink-0 mt-0.5"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>
            <p className="font-semibold text-amber-900 text-sm">
              We're still learning about this organization's finances
            </p>
            {!isOpen && (
              <p className="text-amber-800 text-xs mt-1">
                Click to learn more
              </p>
            )}
          </div>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className={`text-amber-700 flex-shrink-0 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-4 space-y-3 text-sm text-amber-900">
          <p>
            We've classified this organization as <strong>{org.merit_archetype_v5_label}</strong> based on its work category. However, we don't yet have detailed financial data from their IRS filings.
          </p>

          <p className="text-amber-800">
            Many grassroots and community-based nonprofits—especially smaller or newer ones—haven't filed the detailed financial forms we use for peer comparison. That tells us about filing status, not quality or management.
          </p>

          <div className="bg-white/60 p-3 rounded border border-amber-100">
            <p className="font-semibold mb-2 text-amber-900">What this means for you:</p>
            <ul className="space-y-1 text-amber-800 text-xs">
              <li>
                • <strong>Their impact isn't determined by revenue size</strong> — small can mean nimble and community-rooted
              </li>
              <li>
                • <strong>Their financial stability could be excellent</strong> — we just don't have the data yet
              </li>
              <li>
                • <strong>Their own financial story is the best source</strong> — reach out and ask
              </li>
            </ul>
          </div>

          <p className="text-amber-700 text-xs italic">
            We follow Stewardship Charter Principle #7: "Where our data is thin, we say we don't know enough, never they failed."
          </p>
        </div>
      )}
    </div>
  )
}
