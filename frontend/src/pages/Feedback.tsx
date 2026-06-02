import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { submitFeedback } from '../data/api'

export default function Feedback() {
  const location = useLocation()
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const referrer = new URLSearchParams(location.search).get('from') || ''

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim()) return
    setSending(true)
    setError('')
    try {
      await submitFeedback(message.trim(), email.trim() || undefined, referrer || undefined)
      setDone(true)
    } catch {
      setError('Something went wrong. Please try again, or email hello@daanaa.org.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="max-w-[640px] mx-auto px-6 py-16 sm:py-24">
      {done ? (
        <div className="text-center">
          <div className="w-14 h-14 mx-auto rounded-full bg-soft-gold/15 border border-soft-gold/30 flex items-center justify-center mb-6">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </div>
          <h1 className="font-display italic text-deep-navy text-[30px] mb-3">Thank you</h1>
          <p className="font-body text-[15px] text-cool-grey leading-[1.6]">
            We read every note. {email.trim() ? "We'll keep you posted." : 'It helps us make Daanaa better.'}
          </p>
        </div>
      ) : (
        <>
          <h1 className="font-display italic text-deep-navy text-[34px] sm:text-[40px] tracking-[-0.01em] mb-3">
            Tell us what you think
          </h1>
          <p className="font-body text-[15px] text-cool-grey leading-[1.6] mb-8">
            Daanaa is in early access. What worked, what felt off, what you wish it did —
            it all helps. You can stay anonymous, or leave an email if you'd like us to follow up.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block font-body text-[13px] font-medium text-deep-navy mb-2">
                Your feedback
              </label>
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={6}
                required
                maxLength={4000}
                placeholder="What's on your mind?"
                className="w-full px-4 py-3 rounded-xl bg-white border border-light-grey font-body text-[15px] text-deep-navy placeholder:text-cool-grey/50 outline-none focus:border-soft-gold focus:ring-1 focus:ring-soft-gold/30 transition-colors resize-y"
              />
            </div>

            <div>
              <label className="block font-body text-[13px] font-medium text-deep-navy mb-2">
                Email <span className="text-cool-grey font-normal">(optional — only if you want a reply)</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl bg-white border border-light-grey font-body text-[15px] text-deep-navy placeholder:text-cool-grey/50 outline-none focus:border-soft-gold focus:ring-1 focus:ring-soft-gold/30 transition-colors"
              />
            </div>

            {error && <p className="font-body text-[13px] text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={sending || !message.trim()}
              className="inline-flex items-center justify-center px-7 py-3 rounded-full bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
            >
              {sending ? 'Sending…' : 'Send feedback'}
            </button>

            <p className="font-body text-[12px] text-cool-grey/70 leading-[1.5] pt-2">
              We never collect your IP, never track you, and store nothing beyond this
              message and the email you choose to share. Private by design.
            </p>
          </form>
        </>
      )}
    </div>
  )
}
