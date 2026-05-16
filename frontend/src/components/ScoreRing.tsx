import { useEffect, useRef, useState } from 'react'

const TIERS = [
  { range: '90–100', label: 'Exceptional',     color: '#22c55e', desc: 'Top 10% of peers' },
  { range: '75–89',  label: 'High Impact',     color: '#84cc16', desc: 'Well above median' },
  { range: '60–74',  label: 'Solid Performer', color: '#eab308', desc: 'Above median' },
  { range: '40–59',  label: 'Developing',      color: '#f97316', desc: 'Near median' },
  { range: '0–39',   label: 'Needs Data',      color: '#6b7280', desc: 'Limited history' },
]

interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
  label?: string
  badge?: string
  animate?: boolean
  scoreSize?: string
  peerContext?: string   // e.g. "847 Medium-sized B24 nonprofits"
}

export default function ScoreRing({
  score,
  size = 120,
  strokeWidth = 6,
  label = 'MERIT SCORE',
  badge,
  animate = true,
  scoreSize = '32px',
  peerContext,
}: ScoreRingProps) {
  const [animatedScore, setAnimatedScore] = useState(animate ? 0 : score)
  const [progress, setProgress]           = useState(animate ? 0 : score)
  const [showInfo, setShowInfo]           = useState(false)
  const svgRef  = useRef<SVGSVGElement>(null)
  const infoRef = useRef<HTMLDivElement>(null)
  const hasAnimated = useRef(false)

  const radius       = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset       = circumference * (1 - progress / 100)

  // Animate on enter
  useEffect(() => {
    if (!animate || hasAnimated.current) {
      setAnimatedScore(score)
      setProgress(score)
      return
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          const duration  = 1500
          const startTime = performance.now()
          const tick = (now: number) => {
            const t      = Math.min((now - startTime) / duration, 1)
            const eased  = 1 - Math.pow(1 - t, 3)
            setAnimatedScore(Math.round(score * eased))
            setProgress(score * eased)
            if (t < 1) requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
          observer.disconnect()
        }
      },
      { threshold: 0.3 }
    )
    if (svgRef.current) observer.observe(svgRef.current)
    return () => observer.disconnect()
  }, [score, animate])

  // Close info panel on outside click
  useEffect(() => {
    if (!showInfo) return
    const handler = (e: MouseEvent) => {
      if (infoRef.current && !infoRef.current.contains(e.target as Node)) {
        setShowInfo(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showInfo])

  const activeTier = TIERS.find(t => {
    const [lo, hi] = t.range.split('–').map(Number)
    return score >= lo && score <= hi
  }) ?? TIERS[TIERS.length - 1]

  return (
    <div className="flex flex-col items-center gap-2 relative" ref={infoRef}>
      {/* Ring */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg ref={svgRef} width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#1A2744" strokeWidth={strokeWidth} />
          <circle
            cx={size/2} cy={size/2} r={radius} fill="none"
            stroke="#C9A96E" strokeWidth={strokeWidth} strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={offset}
            transform={`rotate(-90 ${size/2} ${size/2})`}
            style={{ transition: animate ? undefined : 'stroke-dashoffset 1.5s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-body font-bold tracking-[-0.03em] text-warm-cream" style={{ fontSize: scoreSize }}>
            {animatedScore}
          </span>
        </div>
      </div>

      {/* Label row with info trigger */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-1.5">
          <p className="font-body text-[11px] font-medium tracking-[0.08em] text-pale-gold uppercase">
            {label}
          </p>
          <button
            onClick={() => setShowInfo(v => !v)}
            aria-label="What is this score?"
            className="w-4 h-4 rounded-full border border-pale-gold/40 text-pale-gold/60 hover:border-soft-gold hover:text-soft-gold transition-colors flex items-center justify-center"
          >
            <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
          </button>
        </div>
        {badge && (
          <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full bg-success-green/20 text-success-green text-[11px] font-medium tracking-[0.02em]">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {badge}
          </span>
        )}
      </div>

      {/* Info panel */}
      {showInfo && (
        <div className="absolute top-full mt-3 left-1/2 -translate-x-1/2 z-50 w-[280px] bg-white rounded-xl shadow-xl border border-light-grey p-4 text-left">
          {/* Arrow */}
          <div className="absolute -top-[6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-l border-t border-light-grey rotate-45" />

          <p className="font-body text-[13px] font-semibold text-deep-navy mb-1">What is this score?</p>
          <p className="font-body text-[12px] text-cool-grey leading-[1.5] mb-3">
            {peerContext
              ? <>A peer percentile — ranked against <strong className="text-deep-navy">{peerContext}</strong>. Higher means stronger financial performance relative to similar organizations.</>
              : <>A peer percentile ranking this organization against nonprofits of similar type and size. Higher means stronger financial performance relative to similar organizations.</>
            }
          </p>

          {/* Tier table */}
          <div className="space-y-1 border-t border-light-grey pt-3">
            {TIERS.map(tier => (
              <div
                key={tier.range}
                className={`flex items-center gap-2 px-2 py-1 rounded-md transition-colors ${tier.label === activeTier.label ? 'bg-soft-gold/10' : ''}`}
              >
                <span className="font-body text-[10px] font-semibold w-12 shrink-0" style={{ color: tier.color }}>
                  {tier.range}
                </span>
                <span className="font-body text-[11px] font-medium text-deep-navy w-28 shrink-0">
                  {tier.label}
                </span>
                <span className="font-body text-[11px] text-cool-grey">
                  {tier.desc}
                </span>
                {tier.label === activeTier.label && (
                  <svg className="ml-auto shrink-0" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                )}
              </div>
            ))}
          </div>

          <a href="/how-it-works" className="mt-3 flex items-center gap-1 font-body text-[11px] text-soft-gold hover:text-bright-gold transition-colors">
            How scoring works →
          </a>
        </div>
      )}
    </div>
  )
}
