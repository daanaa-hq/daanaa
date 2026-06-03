import React from 'react'

export interface ClaimProgressBarProps {
  currentStep: 'email' | 'verify' | 'edit' | 'success'
}

const STEPS = [
  { key: 'email', label: 'Email' },
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
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-body text-[13px] font-bold transition-colors ${
                idx < currentIndex ? 'bg-soft-gold text-deep-navy' :
                idx === currentIndex ? 'bg-deep-navy text-warm-cream' :
                'bg-light-cream text-muted-cream'
              }`}>
                {idx < currentIndex ? '✓' : idx + 1}
              </div>
              <span className={`mt-1 font-body text-[11px] whitespace-nowrap ${
                idx === currentIndex ? 'text-deep-navy font-semibold' : 'text-muted-cream'
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
