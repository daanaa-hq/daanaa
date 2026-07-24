import React from 'react'
import { Check } from 'lucide-react'

interface DiscoveryChoiceProps {
  id: string
  label: string
  description?: string
  selected: boolean
  icon?: React.ReactNode
  onChange: (selected: boolean) => void
  multiSelect?: boolean
}

export const DiscoveryChoice: React.FC<DiscoveryChoiceProps> = ({
  id,
  label,
  description,
  selected,
  icon,
  onChange,
  multiSelect = false,
}) => {
  return (
    <button
      onClick={() => onChange(!selected)}
      className={`
        relative w-full text-left p-4 rounded-lg border-2 transition-all
        ${
          selected
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
        }
        focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2
      `}
      aria-pressed={selected}
      role="checkbox"
      aria-label={`${label}${description ? `: ${description}` : ''}`}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox or radio indicator */}
        <div
          className={`
            flex-shrink-0 mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center
            ${
              selected
                ? 'border-blue-500 bg-blue-500'
                : 'border-gray-300 dark:border-gray-600'
            }
          `}
        >
          {selected && <Check className="w-3 h-3 text-white" />}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {icon && <span className="flex-shrink-0 text-lg">{icon}</span>}
            <h3 className="font-medium text-gray-900 dark:text-white">{label}</h3>
          </div>
          {description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
          )}
        </div>
      </div>
    </button>
  )
}
