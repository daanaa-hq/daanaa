import { useState } from 'react'

export default function BetaBanner() {
  const [dismissed, setDismissed] = useState(() =>
    sessionStorage.getItem('beta-banner-dismissed') === '1'
  )

  if (dismissed) return null

  return (
    <div
      className="relative z-[60] flex items-center justify-center gap-3 px-4 py-2 text-center"
      style={{ backgroundColor: '#0A1628', borderBottom: '1px solid rgba(201,169,110,0.2)' }}
    >
      <span
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.08em] uppercase"
        style={{ background: 'rgba(201,169,110,0.15)', color: '#C9A96E', border: '1px solid rgba(201,169,110,0.3)' }}
      >
        Beta
      </span>
      <p className="font-body text-[12px] text-muted-cream">
        Daanaa is in early access — data is real, some features are still being refined.{' '}
        <a
          href="mailto:hello@daanaa.org?subject=Daanaa feedback"
          className="underline underline-offset-2 hover:text-warm-cream transition-colors"
          style={{ color: '#C9A96E' }}
        >
          Share feedback
        </a>
      </p>
      <button
        onClick={() => {
          sessionStorage.setItem('beta-banner-dismissed', '1')
          setDismissed(true)
        }}
        aria-label="Dismiss beta notice"
        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 opacity-50 hover:opacity-100 transition-opacity"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#F5F0EB" strokeWidth="2">
          <line x1="4" y1="4" x2="20" y2="20" /><line x1="20" y1="4" x2="4" y2="20" />
        </svg>
      </button>
    </div>
  )
}
