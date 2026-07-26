interface AiBadgeProps {
  title?: string
  className?: string
}

export default function AiBadge({ title, className = '' }: AiBadgeProps) {
  return (
    <span
      title={title ?? 'This description was written by AI from public IRS records. It has not been confirmed by the organization. Verify details directly with them before making any decisions.'}
      className={`border border-muted-cream/60 text-muted-cream rounded text-micro px-1.5 py-0.5 font-body tracking-[0.04em] ${className}`}
    >
      AI assisted
    </span>
  )
}
