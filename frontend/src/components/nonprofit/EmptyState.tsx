interface EmptyStateProps {
  type: 'no-approvals' | 'no-feedback' | 'no-events' | 'no-changes' | 'profile-complete'
  onAction?: () => void
  actionLabel?: string
}

const emptyStates: Record<string, { icon: string; title: string; message: string; suggestedAction?: string }> = {
  'no-approvals': {
    icon: '✓',
    title: 'All caught up!',
    message: 'No volunteer hours waiting for approval. Keep sharing your events to attract more volunteers.',
    suggestedAction: 'Create a new event'
  },
  'no-feedback': {
    icon: '💬',
    title: 'No feedback yet',
    message: 'When donors visit your profile, they can leave feedback. Keep improving your organization.',
    suggestedAction: 'Complete your profile'
  },
  'no-events': {
    icon: '📅',
    title: 'No events yet',
    message: 'Create volunteer opportunities for donors to contribute their time and skills.',
    suggestedAction: 'Create your first event'
  },
  'no-changes': {
    icon: '📝',
    title: 'No changes yet',
    message: 'You haven\'t edited your profile yet. Update your information to help donors understand your work.',
    suggestedAction: 'Edit your profile'
  },
  'profile-complete': {
    icon: '🎉',
    title: 'Your profile is complete!',
    message: 'Great work! Your organization profile has all the essential information donors need to understand your mission.',
    suggestedAction: undefined
  }
}

export default function EmptyState({
  type,
  onAction,
  actionLabel
}: EmptyStateProps) {
  const state = emptyStates[type]
  const label = actionLabel || state.suggestedAction

  return (
    <div className="text-center py-12 px-6">
      <div className="text-6xl mb-4">{state.icon}</div>
      <h3 className="font-display text-xl text-deep-navy mb-2">{state.title}</h3>
      <p className="font-body text-[14px] text-cool-grey mb-6 max-w-md mx-auto leading-relaxed">
        {state.message}
      </p>
      {label && onAction && (
        <button
          onClick={onAction}
          className="inline-block px-6 py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition"
          aria-label={label}
        >
          {label}
        </button>
      )}
    </div>
  )
}
