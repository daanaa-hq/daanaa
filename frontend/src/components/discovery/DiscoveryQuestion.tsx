import React from 'react'
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react'

interface DiscoveryQuestionProps {
  heading: string
  subheading?: string
  children: React.ReactNode
  onBack?: () => void
  onContinue?: () => void
  onStartOver?: () => void
  canContinue?: boolean
  showBack?: boolean
  showStartOver?: boolean
  continueLabel?: string
}

export const DiscoveryQuestion: React.FC<DiscoveryQuestionProps> = ({
  heading,
  subheading,
  children,
  onBack,
  onContinue,
  onStartOver,
  canContinue = true,
  showBack = true,
  showStartOver = false,
  continueLabel = 'Continue',
}) => {
  return (
    <div className="max-w-2xl mx-auto px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          {heading}
        </h1>
        {subheading && (
          <p className="text-lg text-gray-600 dark:text-gray-400">{subheading}</p>
        )}
      </div>

      {/* Choices */}
      <div className="mb-10">{children}</div>

      {/* Navigation */}
      <div className="flex items-center gap-3 justify-between">
        <div className="flex gap-2">
          {showBack && onBack && (
            <button
              onClick={onBack}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              aria-label="Go back to previous question"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
          )}
          {showStartOver && onStartOver && (
            <button
              onClick={onStartOver}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              aria-label="Start over from the beginning"
            >
              <RotateCcw className="w-4 h-4" />
              Start over
            </button>
          )}
        </div>

        {onContinue && (
          <button
            onClick={onContinue}
            disabled={!canContinue}
            className={`
              inline-flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors
              ${
                canContinue
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {continueLabel}
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
