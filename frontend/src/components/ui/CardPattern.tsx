import React from 'react'

/**
 * CardPattern — lightweight wrapper for consistent card styling across the app.
 * Use this for all inline card-like divs instead of raw className patterns.
 */

interface CardPatternProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'default' | 'subtle' | 'elevated' | 'nested' | 'gradient'
}

const cardVariants = {
  default: 'bg-white rounded-lg border border-light-grey p-6',
  subtle: 'bg-warm-cream/40 rounded-lg border border-light-grey p-6',
  elevated: 'bg-white rounded-2xl border border-light-grey p-6 hover:border-soft-gold/40 transition-colors',
  nested: 'bg-white rounded-md border border-light-grey p-4',
  gradient: 'rounded-lg border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6',
}

export function CardPattern({ variant = 'default', className, children, ...props }: CardPatternProps) {
  const baseClass = cardVariants[variant]
  const finalClass = className ? `${baseClass} ${className}` : baseClass

  return (
    <div className={finalClass} {...props}>
      {children}
    </div>
  )
}

/**
 * Utility: CardGrid — container for multiple cards in a grid
 */
interface CardGridProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function CardGrid({ className, children, ...props }: CardGridProps) {
  const defaultClass = 'grid gap-4 md:gap-6'
  const finalClass = className ? `${defaultClass} ${className}` : defaultClass

  return (
    <div className={finalClass} {...props}>
      {children}
    </div>
  )
}
