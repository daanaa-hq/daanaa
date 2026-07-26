import * as React from 'react'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'

const CONTENT_CLASS =
  'z-50 max-w-[260px] rounded-lg bg-deep-navy px-3 py-2 text-caption leading-relaxed ' +
  'text-warm-cream/90 shadow-lg border border-soft-gold/30 ' +
  'animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0'

function Body({ tip, children }: { tip: React.ReactNode; children: React.ReactNode }) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content sideOffset={6} className={CONTENT_CLASS}>
        {tip}
        <TooltipPrimitive.Arrow className="fill-[#0A1628]" />
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  )
}

/**
 * Inline glossary term. Renders the word(s) with a faint dotted underline and a
 * help cursor; hovering or focusing reveals a definition. Keeps the user on the
 * page instead of navigating away. Definitions should mirror the research /
 * methodology pages so the product tells one consistent story.
 */
export function InfoTerm({
  children,
  tip,
}: {
  children: React.ReactNode
  tip: React.ReactNode
}) {
  return (
    <TooltipPrimitive.Provider delayDuration={150}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          <span
            tabIndex={0}
            role="button"
            aria-label="Show definition"
            className="underline decoration-dotted decoration-cool-grey/40 underline-offset-[3px] cursor-help focus:outline-none focus-visible:ring-1 focus-visible:ring-soft-gold rounded-sm"
          >
            {children}
          </span>
        </TooltipPrimitive.Trigger>
        <Body tip={tip}>{children}</Body>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}

/**
 * Wraps an arbitrary element (e.g. a badge or stat) as a tooltip trigger without
 * adding a dotted underline — for things that already read as interactive.
 */
export function InfoTip({
  children,
  tip,
}: {
  children: React.ReactNode
  tip: React.ReactNode
}) {
  return (
    <TooltipPrimitive.Provider delayDuration={150}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          <span tabIndex={0} aria-label="Show definition" className="cursor-help focus:outline-none focus-visible:ring-1 focus-visible:ring-soft-gold rounded-full">
            {children}
          </span>
        </TooltipPrimitive.Trigger>
        <Body tip={tip}>{children}</Body>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}
