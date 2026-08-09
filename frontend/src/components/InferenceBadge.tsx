import React from 'react'
import { Info } from 'lucide-react'

interface InferenceBadgeProps {
  peerCount: number
  confidence: 'good' | 'moderate'
  peerGroupDescription: string
}

/**
 * InferenceBadge — displays when an org's peer comparison widened beyond its
 * narrowest possible peer group (Regional Context or Broad Category tier).
 * Shows that the comparison group is broader than the tightest one, not a
 * verdict on this org's own finances.
 */
export default function InferenceBadge({
  peerCount,
  confidence,
  peerGroupDescription,
}: InferenceBadgeProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-md">
      <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />

      <div className="flex-1 text-sm">
        <span className="text-gray-700">
          Context based on <strong>{peerCount} similar organizations</strong>
        </span>

        {/* Tooltip on hover */}
        <div className="hidden group-hover:block absolute bg-gray-900 text-white text-xs px-3 py-2 rounded shadow-lg z-10 w-64">
          <p className="font-semibold mb-1">What does this mean?</p>
          <p className="mb-2">The narrowest peer group (same type, size, and region) was too small for a meaningful comparison, so this compares against a broader group instead.</p>
          <p className="mb-2">Peer group: {peerGroupDescription}</p>
          <p className="mb-2">Confidence: {confidence}</p>
          <p className="text-xs text-gray-300 mt-2">This describes similar organizations, not this organization's own finances.</p>
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
