import React from 'react'
import { Info } from 'lucide-react'

type ConfidenceLevel = 'high' | 'good' | 'low'

interface ConfidenceBadgeProps {
  level: ConfidenceLevel
  showTooltip?: boolean
  className?: string
}

/**
 * Confidence badge for org financial data (Stewardship P3: Evidence-Based)
 * Shows confidence level based on data source:
 * - High: Direct IRS Form 990 data (recent filing)
 * - Good: NTEE peer-group estimate (no recent 990)
 * - Low: No ranking data available
 */
export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  level,
  showTooltip = true,
  className = '',
}) => {
  const config = {
    high: {
      label: 'High Confidence',
      badge: 'bg-green-50/80 text-green-700 border-green-200',
      icon: '✓',
      tooltip:
        'Direct IRS Form 990 filing data. We have their recent financial records.',
      percentage: '17.9%',
    },
    good: {
      label: 'Good Confidence',
      badge: 'bg-yellow-50/80 text-yellow-700 border-yellow-200',
      icon: '≈',
      tooltip:
        'Estimated from peer group. Similar orgs in same category provide context.',
      percentage: '13.1%',
    },
    low: {
      label: 'Limited Data',
      badge: 'bg-slate-50/80 text-slate-600 border-slate-200',
      icon: '?',
      tooltip:
        'No financial ranking available. Focus on mission, website, and direct contact.',
      percentage: '68.9%',
    },
  }

  const conf = config[level]

  return (
    <div className={`relative inline-flex items-center gap-1 ${className}`}>
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${conf.badge}`}
        title={showTooltip ? conf.tooltip : ''}
      >
        <span className="text-sm">{conf.icon}</span>
        <span>{conf.label}</span>
        <span className="text-[11px] opacity-75">({conf.percentage})</span>
      </div>

      {showTooltip && (
        <div className="hidden group-hover:block absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-max bg-slate-900 text-white text-xs rounded px-2 py-1 pointer-events-none z-10">
          {conf.tooltip}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-slate-900" />
        </div>
      )}
    </div>
  )
}

export default ConfidenceBadge
