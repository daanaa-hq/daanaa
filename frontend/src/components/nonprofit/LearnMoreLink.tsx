interface LearnMoreLinkProps {
  text?: string
  topic: 'volunteer-approval' | 'profile-sources' | 'financial-health' | 'donation-link' | 'data-freshness'
  onClick?: () => void
  inline?: boolean
}

const topicMap: Record<string, { text: string; description: string }> = {
  'volunteer-approval': {
    text: 'Learn about volunteer approval',
    description: 'How the approval process works and timelines'
  },
  'profile-sources': {
    text: 'Learn about data sources',
    description: 'What "IRS," "nonprofit-supplied," and "AI-generated" mean'
  },
  'financial-health': {
    text: 'Learn about financial context',
    description: 'How your V6 financial context is calculated'
  },
  'donation-link': {
    text: 'Learn about donation links',
    description: 'How donors find and use your donation link'
  },
  'data-freshness': {
    text: 'Learn about data updates',
    description: 'When and how your information updates'
  }
}

export default function LearnMoreLink({
  text,
  topic,
  onClick,
  inline = false
}: LearnMoreLinkProps) {
  const topicInfo = topicMap[topic]
  const displayText = text || topicInfo.text

  const handleClick = () => {
    if (onClick) {
      onClick()
    }
  }

  if (inline) {
    return (
      <button
        onClick={handleClick}
        className="inline-flex items-center gap-1 text-soft-gold hover:text-bright-gold font-body text-small font-semibold underline hover:no-underline transition"
        title={topicInfo.description}
        type="button"
      >
        {displayText}
        <span aria-hidden="true" className="text-label">→</span>
      </button>
    )
  }

  return (
    <button
      onClick={handleClick}
      className="w-full p-3 rounded-lg border border-soft-gold/50 hover:border-soft-gold hover:bg-soft-gold/5 transition text-left"
      type="button"
      aria-label={displayText}
      title={topicInfo.description}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-body text-small font-semibold text-deep-navy">{displayText}</p>
          <p className="font-body text-label text-cool-grey mt-0.5">{topicInfo.description}</p>
        </div>
        <span className="text-soft-gold text-lg flex-shrink-0" aria-hidden="true">→</span>
      </div>
    </button>
  )
}
