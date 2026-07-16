import { useState } from 'react'

// An easy, anonymous way for a visitor to tell an organization "I'd volunteer
// with you" — even before the org has claimed its page. We store only an
// aggregate count (no identity, no contact). The org sees the tally when it
// claims, as a reason to claim and a place to start. Giving-intent signals were
// removed 2026-06-10: Daanaa carries no donation prompts on public surfaces.

export default function SupportIntent({ orgName, ein }: { orgName: string; ein: string }) {
  const [sent, setSent] = useState(false)

  const signal = () => {
    setSent(true)
    try {
      const body = JSON.stringify({ ein, kind: 'volunteer' })
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/interest', new Blob([body], { type: 'application/json' }))
      } else {
        fetch('/api/interest', { method: 'POST', body, headers: { 'Content-Type': 'application/json' }, keepalive: true }).catch(() => {})
      }
    } catch { /* ignore */ }
  }

  if (sent) {
    return (
      <p className="font-body text-[12px] text-cool-grey leading-[1.5]">
        Thank you. When {orgName} claims their page, they'll see there's interest in
        volunteering, anonymously. We never store who you are.
      </p>
    )
  }

  return (
    <div>
      <p className="font-body text-[12px] text-cool-grey mb-2 leading-[1.5]">
        Want to support {orgName}? Let them know there's interest, anonymously.
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={signal}
          className="rounded-full border border-deep-gold/50 px-3.5 py-1.5 font-body text-[12px] font-medium text-deep-gold hover:bg-soft-gold/10 transition-colors"
        >
          I'd volunteer here
        </button>
      </div>
    </div>
  )
}
