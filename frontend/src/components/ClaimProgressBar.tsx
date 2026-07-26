import React from 'react'

export interface ClaimProgressBarProps {
  currentStep: 'email' | 'verify' | 'edit' | 'success'
}

const STEPS = [
  { key: 'email', label: 'Submit' },
  { key: 'verify', label: 'Verify PIN' },
  { key: 'edit', label: 'Edit Profile' },
  { key: 'success', label: 'Done' },
]

export function ClaimProgressBar({ currentStep }: ClaimProgressBarProps) {
  const currentIndex = STEPS.findIndex(s => s.key === currentStep)
  return (
    <div className="w-full mb-8">
      <div className="flex items-center gap-0">
        {STEPS.map((step, idx) => (
          <React.Fragment key={step.key}>
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-body text-small font-bold transition-colors ${
                idx < currentIndex ? 'bg-soft-gold text-deep-navy' :
                idx === currentIndex ? 'bg-deep-navy text-warm-cream' :
                'bg-navy-mid text-cool-grey'
              }`}>
                {idx < currentIndex ? '✓' : idx + 1}
              </div>
              <span className={`mt-1 font-body text-label whitespace-nowrap ${
                idx === currentIndex ? 'text-warm-cream font-semibold' : 'text-cool-grey'
              }`}>{step.label}</span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mb-5 transition-colors ${idx < currentIndex ? 'bg-soft-gold' : 'bg-light-cream'}`} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
