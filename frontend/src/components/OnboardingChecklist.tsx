import React, { useState, useEffect } from 'react'

interface ChecklistItem {
  id: string
  label: string
  description: string
  completed: boolean
  action?: { label: string; href: string }
}

interface OnboardingChecklistProps {
  ein: string
  onDismiss?: () => void
}

export default function OnboardingChecklist({ ein, onDismiss }: OnboardingChecklistProps) {
  const [items, setItems] = useState<ChecklistItem[]>([
    {
      id: 'email-verified',
      label: 'Email verified',
      description: 'Your nonprofit account is set up',
      completed: true,
    },
    {
      id: 'letters-ready',
      label: 'Donation letters enabled',
      description: 'You can approve and generate donation letters for donors (coming soon)',
      completed: false,
    },
    {
      id: 'volunteer-hours',
      label: 'Volunteer hours tracking',
      description: 'Track and verify volunteer service hours',
      completed: false,
      action: { label: 'Set up', href: `/nonprofit/volunteer-approval` },
    },
    {
      id: 'daanaa-profile',
      label: 'Daanaa profile optimized',
      description: 'Your organization info is complete on Daanaa',
      completed: false,
      action: { label: 'View profile', href: `/org/${ein}` },
    },
  ])

  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    const dismissedKey = `onboarding_dismissed_${ein}`
    const wasDismissed = localStorage.getItem(dismissedKey) === 'true'
    setDismissed(wasDismissed)
  }, [ein])

  const completedCount = items.filter(i => i.completed).length

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem(`onboarding_dismissed_${ein}`, 'true')
    if (onDismiss) onDismiss()
  }

  if (dismissed) return null

  return (
    <div className="bg-gradient-to-r from-soft-gold/10 to-bright-gold/10 border border-soft-gold/30 rounded-2xl p-6 mb-8">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="font-display text-2xl text-deep-navy mb-1">Get started</h2>
          <p className="text-sm text-cool-grey">
            {completedCount}/{items.length} steps complete
          </p>
        </div>
        <button
          onClick={handleDismiss}
          className="text-cool-grey hover:text-deep-navy transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-soft-gold/20 rounded-full h-2 mb-6">
        <div
          className="bg-soft-gold h-2 rounded-full transition-all"
          style={{ width: `${(completedCount / items.length) * 100}%` }}
        />
      </div>

      {/* Checklist items */}
      <div className="space-y-3">
        {items.map(item => (
          <div
            key={item.id}
            className="flex items-start gap-3 p-3 bg-white/60 rounded-lg hover:bg-white/80 transition-colors"
          >
            <div className="flex-shrink-0 mt-1">
              {item.completed ? (
                <div className="w-5 h-5 rounded-full bg-soft-gold flex items-center justify-center">
                  <svg className="w-3 h-3 text-deep-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-cool-grey/30" />
              )}
            </div>
            <div className="flex-1">
              <p className={`font-semibold text-sm ${item.completed ? 'text-cool-grey line-through' : 'text-deep-navy'}`}>
                {item.label}
              </p>
              <p className="text-xs text-cool-grey mt-0.5">{item.description}</p>
            </div>
            {item.action && !item.completed && (
              <a
                href={item.action.href}
                className="flex-shrink-0 px-3 py-1 bg-soft-gold text-deep-navy text-xs font-semibold rounded-lg hover:bg-bright-gold transition-colors whitespace-nowrap"
              >
                {item.action.label}
              </a>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-soft-gold/10 rounded-lg border border-soft-gold/30">
        <p className="font-body text-sm text-deep-navy">
          <strong>Tip:</strong> Setting up volunteer hours tracking helps donors understand the community impact behind your work.
        </p>
      </div>
    </div>
  )
}
