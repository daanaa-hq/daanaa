import React from 'react'
import { Info } from 'lucide-react'

interface InferenceBadgeProps {
  peerCount: number
  confidence: 'good' | 'moderate'
  peerGroupDescription: string
  confidenceMargin?: string
}

/**
 * InferenceBadge — displays when Tier 2 org has inferred (not direct) financial context
 * Shows that data comes from peer group, not this org's actual 990 filing
 */
export default function InferenceBadge({
  peerCount,
  confidence,
  peerGroupDescription,
  confidenceMargin = '±10%',
}: InferenceBadgeProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-md">
      <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />

      <div className="flex-1 text-sm">
        <span className="text-gray-700">
          Context based on <strong>{peerCount} similar organizations</strong> in this region and category
        </span>

        {/* Tooltip on hover */}
        <div className="hidden group-hover:block absolute bg-gray-900 text-white text-xs px-3 py-2 rounded shadow-lg z-10 w-64">
          <p className="font-semibold mb-1">What does this mean?</p>
          <p className="mb-2">This organization hasn't filed recent financial data with the IRS. We're showing typical financial practices for similar nonprofits in your region.</p>
          <p className="mb-2">Peer group: {peerGroupDescription}</p>
          <p className="mb-2">Confidence: {confidence} (margin: {confidenceMargin})</p>
          <p className="text-xs text-gray-300 mt-2">We recommend asking this organization directly about their actual financial practices.</p>
        </div>
      </div>

      {/* Confidence indicator */}
      <div className={`text-xs font-medium px-2 py-1 rounded ${
        confidence === 'good'
          ? 'bg-blue-100 text-blue-700'
          : 'bg-amber-100 text-amber-700'
      }`}>
        {confidence === 'good' ? 'Good confidence' : 'Moderate confidence'}
      </div>
    </div>
  )
}
