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
        <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
          Step {currentStep} of {totalSteps}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-500">
          {Math.round((currentStep / totalSteps) * 100)}%
        </div>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
        <div
          className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
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
