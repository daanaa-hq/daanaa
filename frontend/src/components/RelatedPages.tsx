import { Link } from 'react-router-dom'

export interface RelatedLink {
  to: string
  label: string
}

/**
 * Standardized "Learn more" footer that connects the content/story pages
 * (About, Methodology, Research, Principles, …) so each one hands off to the
 * next and the product tells one consistent story. Matches the existing pattern
 * on the Principles and Methodology pages.
 */
export default function RelatedPages({
  links,
  heading = 'Learn more',
}: {
  links: RelatedLink[]
  heading?: string
}) {
  if (!links.length) return null
  return (
    <div className="mt-16 pt-8 border-t border-light-grey">
      <p className="font-body text-[12px] font-semibold tracking-[0.08em] text-cool-grey uppercase mb-4">
        {heading}
      </p>
      <div className="flex flex-wrap gap-x-6 gap-y-3">
        {links.map((l) => (
          <Link
            key={l.to + l.label}
            to={l.to}
            className="inline-flex items-center gap-2 font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors"
          >
            {l.label} →
          </Link>
        ))}
      </div>
    </div>
  )
}
