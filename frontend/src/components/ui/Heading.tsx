import React from 'react'

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6

interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: HeadingLevel
  children: React.ReactNode
}

const headingClasses: Record<HeadingLevel, string> = {
  1: 'font-display italic text-deep-navy text-4xl md:text-5xl',
  2: 'font-display italic text-deep-navy text-3xl md:text-4xl',
  3: 'font-display italic text-deep-navy text-2xl md:text-3xl',
  4: 'font-display text-deep-navy text-xl md:text-2xl font-semibold',
  5: 'font-display text-deep-navy text-lg md:text-xl font-semibold',
  6: 'font-body text-deep-navy text-base md:text-lg font-semibold uppercase tracking-widest',
}

const Heading = React.forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ level = 2, className, children, ...props }, ref) => {
    const Tag = `h${level}` as const
    const baseClass = headingClasses[level]

    return React.createElement(
      Tag,
      {
        ref,
        className: `${baseClass} ${className || ''}`,
        ...props,
      },
      children
    )
  }
)
Heading.displayName = 'Heading'

export { Heading }