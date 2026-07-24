import React from 'react'

interface DiscoveryProgressProps {
  currentStep: 1 | 2 | 3 | 4 | 5
  totalSteps?: number
}

export const DiscoveryProgress: React.FC<DiscoveryProgressProps> = ({
  currentStep,
  totalSteps = 5,
}) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-medium text-cool-grey">
          Step {currentStep} of {totalSteps}
        </div>
        <div className="text-xs text-cool-grey">
          {Math.round((currentStep / totalSteps) * 100)}%
        </div>
      </div>
      <div className="w-full bg-light-grey rounded-full h-1.5">
        <div
          className="bg-soft-gold h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          role="progressbar"
          aria-valuenow={currentStep}
          aria-valuemin={1}
          aria-valuemax={totalSteps}
        />
      </div>
    </div>
  )
}
