import { useState } from 'react'

interface RevenueRangeInputProps {
  min: number
  max: number
  onMinChange: (value: number) => void
  onMaxChange: (value: number) => void
}

const MIN_BOUND = 0
const MAX_BOUND = 500_000_000

function formatDisplay(value: number) {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(0)}M`
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`
  }
  return `$${value}`
}

function parseInput(str: string): number | null {
  const cleaned = str.replace(/[^\d]/g, '')
  const num = parseInt(cleaned, 10)
  return isNaN(num) ? null : num
}

export default function RevenueRangeInput({
  min,
  max,
  onMinChange,
  onMaxChange,
}: RevenueRangeInputProps) {
  const [minInput, setMinInput] = useState(formatDisplay(min))
  const [maxInput, setMaxInput] = useState(formatDisplay(max))

  const handleMinChange = (value: string) => {
    setMinInput(value)
    const parsed = parseInput(value)
    if (parsed !== null) {
      const clamped = Math.min(Math.max(parsed, MIN_BOUND), max)
      onMinChange(clamped)
    }
  }

  const handleMaxChange = (value: string) => {
    setMaxInput(value)
    const parsed = parseInput(value)
    if (parsed !== null) {
      const clamped = Math.max(Math.min(parsed, MAX_BOUND), min)
      onMaxChange(clamped)
    }
  }

  const minPercent = ((min - MIN_BOUND) / (MAX_BOUND - MIN_BOUND)) * 100
  const maxPercent = ((max - MIN_BOUND) / (MAX_BOUND - MIN_BOUND)) * 100

  return (
    <div className="space-y-3">
      {/* Input fields */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="font-body text-[11px] font-semibold text-cool-grey uppercase block mb-1.5">Min</label>
          <input
            type="text"
            value={minInput}
            onChange={(e) => handleMinChange(e.target.value)}
            onBlur={() => setMinInput(formatDisplay(min))}
            placeholder="$0"
            className="w-full h-[44px] px-3 rounded-lg bg-warm-cream border border-light-grey font-body text-[14px] font-semibold text-deep-navy outline-none focus:border-soft-gold transition-colors"
          />
        </div>
        <div>
          <label className="font-body text-[11px] font-semibold text-cool-grey uppercase block mb-1.5">Max</label>
          <input
            type="text"
            value={maxInput}
            onChange={(e) => handleMaxChange(e.target.value)}
            onBlur={() => setMaxInput(formatDisplay(max))}
            placeholder="$500M"
            className="w-full h-[44px] px-3 rounded-lg bg-warm-cream border border-light-grey font-body text-[14px] font-semibold text-deep-navy outline-none focus:border-soft-gold transition-colors"
          />
        </div>
      </div>

      {/* Visual range indicator */}
      <div className="relative h-1.5 bg-light-grey rounded-full overflow-hidden">
        <div
          className="absolute h-full bg-soft-gold"
          style={{
            left: `${minPercent}%`,
            right: `${100 - maxPercent}%`,
          }}
        />
      </div>
    </div>
  )
}
