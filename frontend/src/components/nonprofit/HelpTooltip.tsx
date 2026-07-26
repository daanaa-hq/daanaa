import { useState } from 'react'

interface HelpTooltipProps {
  text: string
  children?: React.ReactNode
  side?: 'top' | 'bottom' | 'left' | 'right'
}

export default function HelpTooltip({ text, children, side = 'top' }: HelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)

  const sideClasses = {
    top: 'bottom-full mb-2',
    bottom: 'top-full mt-2',
    left: 'right-full mr-2',
    right: 'left-full ml-2'
  }

  const arrowClasses = {
    top: 'top-full border-t-soft-gold border-l-transparent border-r-transparent border-b-0',
    bottom: 'bottom-full border-b-soft-gold border-l-transparent border-r-transparent border-t-0',
    left: 'left-full border-l-soft-gold border-t-transparent border-b-transparent border-r-0',
    right: 'right-full border-r-soft-gold border-t-transparent border-b-transparent border-l-0'
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-soft-gold/20 text-soft-gold hover:bg-soft-gold/40 transition-colors cursor-help"
        aria-label="More information"
        aria-describedby="help-tooltip"
        type="button"
      >
        <span className="text-caption font-bold">?</span>
      </button>

      {children}

      {isOpen && (
        <div
          id="help-tooltip"
          className={`absolute ${sideClasses[side]} z-50 w-48 px-3 py-2 bg-soft-gold text-deep-navy rounded-lg shadow-lg text-caption font-body leading-relaxed`}
          role="tooltip"
        >
          {text}
          <div
            className={`absolute w-0 h-0 border-4 ${arrowClasses[side]}`}
            aria-hidden="true"
          />
        </div>
      )}
    </div>
  )
}
