import { Link } from 'react-router-dom'

export interface BreadcrumbItem {
  label: string
  href?: string  // omit for current page (non-linked)
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="py-3 px-6 bg-white/50 border-b border-soft-gold/20" aria-label="Breadcrumb">
      <ol className="flex flex-wrap gap-2 text-sm">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-center gap-2">
            {item.href ? (
              <Link to={item.href} className="text-cool-grey hover:text-deep-navy transition-colors underline underline-offset-2">
                {item.label}
              </Link>
            ) : (
              <span className="text-cool-grey font-medium">{item.label}</span>
            )}
            {idx < items.length - 1 && <span className="text-soft-gold">/</span>}
          </li>
        ))}
      </ol>
    </nav>
  )
}
