interface RevenueRangeInputProps {
  min: number
  max: number
  onMinChange: (value: number) => void
  onMaxChange: (value: number) => void
}

const REVENUE_TIERS = [
  { value: 0, label: '$0' },
  { value: 150_000, label: '$150K' },
  { value: 700_000, label: '$700K' },
  { value: 5_000_000, label: '$5M' },
  { value: 25_000_000, label: '$25M' },
  { value: 100_000_000, label: '$100M' },
]

export default function RevenueRangeInput({
  min,
  max,
  onMinChange,
  onMaxChange,
}: RevenueRangeInputProps) {
  const handleMinChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = parseInt(e.target.value, 10)
    onMinChange(value)
  }

  const handleMaxChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value === 'unlimited' ? 500_000_000 : parseInt(e.target.value, 10)
    onMaxChange(value)
  }

  return (
    <div className="space-y-3">
      {/* Dropdown selectors */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="font-body text-[11px] font-semibold text-cool-grey uppercase block mb-1.5">From</label>
          <select
            value={min}
            onChange={handleMinChange}
            className="w-full h-[44px] px-3 rounded-lg bg-warm-cream border border-light-grey font-body text-[14px] font-semibold text-deep-navy outline-none focus:border-soft-gold transition-colors cursor-pointer"
          >
            {REVENUE_TIERS.map((tier) => (
              <option key={tier.value} value={tier.value}>
                {tier.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="font-body text-[11px] font-semibold text-cool-grey uppercase block mb-1.5">To</label>
          <select
            value={max === 500_000_000 ? 'unlimited' : max}
            onChange={handleMaxChange}
            className="w-full h-[44px] px-3 rounded-lg bg-warm-cream border border-light-grey font-body text-[14px] font-semibold text-deep-navy outline-none focus:border-soft-gold transition-colors cursor-pointer"
          >
            {REVENUE_TIERS.map((tier) => (
              <option key={tier.value} value={tier.value}>
                {tier.label}
              </option>
            ))}
            <option value="unlimited">No limit</option>
          </select>
        </div>
      </div>
    </div>
  )
}
