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
        <h1 className="text-3xl font-bold font-display text-deep-navy mb-2">
          {heading}
        </h1>
        {subheading && (
          <p className="text-lg text-cool-grey">{subheading}</p>
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
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy hover:bg-muted-cream transition-colors"
              aria-label="Go back to previous question"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
          )}
          {showStartOver && onStartOver && (
            <button
              onClick={onStartOver}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy hover:bg-muted-cream transition-colors"
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
                  ? 'bg-soft-gold hover:bg-bright-gold text-deep-navy'
                  : 'bg-light-grey text-cool-grey cursor-not-allowed'
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
