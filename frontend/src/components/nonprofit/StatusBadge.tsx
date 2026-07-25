interface StatusBadgeProps {
  status: 'submitted' | 'approved' | 'rejected' | 'pending'
  withContext?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function StatusBadge({ status, withContext = true, size = 'md' }: StatusBadgeProps) {
  const statusConfig = {
    submitted: {
      bgColor: 'bg-alert-amber/5',
      borderColor: 'border-amber-200',
      textColor: 'text-alert-amber',
      icon: '⏳',
      label: 'Submitted',
      context: 'awaiting nonprofit review'
    },
    approved: {
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      textColor: 'text-emerald-900',
      icon: '✓',
      label: 'Approved',
      context: 'counted toward public impact'
    },
    rejected: {
      bgColor: 'bg-destructive/5',
      borderColor: 'border-destructive/20',
      textColor: 'text-red-900',
      icon: '✗',
      label: 'Rejected',
      context: 'nonprofit will follow up'
    },
    pending: {
      bgColor: 'bg-cool-grey/10',
      borderColor: 'border-light-grey',
      textColor: 'text-cool-grey',
      icon: '○',
      label: 'Pending',
      context: 'waiting for submission'
    }
  }

  const config = statusConfig[status]
  const sizeClasses = {
    sm: 'px-2 py-1 text-[11px]',
    md: 'px-3 py-1.5 text-[12px]',
    lg: 'px-4 py-2 text-[13px]'
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border ${config.bgColor} ${config.borderColor} ${config.textColor} font-semibold font-body ${sizeClasses[size]}`}
      role="status"
      aria-label={`Status: ${config.label}${withContext ? ' (' + config.context + ')' : ''}`}
    >
      <span className="leading-none">{config.icon}</span>
      <span>{config.label}</span>
      {withContext && (
        <span className={`ml-1 text-[11px] opacity-75 font-normal`}>
          ({config.context})
        </span>
      )}
    </span>
  )
}
