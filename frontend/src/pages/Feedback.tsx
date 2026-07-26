import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { submitFeedback } from '../data/api'

const CATEGORIES: { value: string; label: string; hint: string }[] = [
  { value: 'general', label: 'General feedback', hint: "What's on your mind?" },
  { value: 'data-issue', label: 'Report a data issue', hint: 'Which organization, and what looks wrong? Include the name or EIN if you can.' },
  { value: 'org', label: 'Claim or correct my organization', hint: "Tell us your organization's name and EIN, and what you'd like updated." },
  { value: 'bug', label: "Something's broken", hint: 'What were you doing, and what happened? A link or page helps.' },
  { value: 'other', label: 'Something else', hint: "What's on your mind?" },
]

export default function Feedback() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const referrer = params.get('from') || ''
  const initialType = params.get('type') || ''

  const [category, setCategory] = useState(
    CATEGORIES.some(c => c.value === initialType) ? initialType : 'general'
  )
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const activeCat = CATEGORIES.find(c => c.value === category) || CATEGORIES[0]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!message.trim()) return
    setSending(true)
    setError('')
    try {
      await submitFeedback(message.trim(), {
        email: email.trim() || undefined,
        page: referrer || undefined,
        category,
      })
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
          <h1 className="font-display italic text-deep-navy text-headline-lg mb-3">Thank you</h1>
          <p className="font-body text-body-lg text-cool-grey leading-[1.6]">
            We read every note. {email.trim() ? "We'll keep you posted." : 'It helps us make Daanaa better.'}
          </p>
        </div>
      ) : (
        <>
          <h1 className="font-display italic text-deep-navy text-headline-lg sm:text-display tracking-[-0.01em] mb-3">
            Tell us what you think
          </h1>
          <p className="font-body text-body-lg text-cool-grey leading-[1.6] mb-8">
            Daanaa is in early access. Found wrong data, want to fix your organization's page,
            or just have a thought? Pick what fits below. You can stay anonymous, or leave an
            email if you'd like us to follow up.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block font-body text-small font-medium text-deep-navy mb-2">
                What's this about?
              </label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white border border-light-grey font-body text-body-lg text-deep-navy outline-none focus:border-soft-gold focus:ring-1 focus:ring-soft-gold/30 transition-colors appearance-none cursor-pointer"
                style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'14\' height=\'14\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%236B7280\' stroke-width=\'2\'%3E%3Cpolyline points=\'6 9 12 15 18 9\'/%3E%3C/svg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center' }}
              >
                {CATEGORIES.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-body text-small font-medium text-deep-navy mb-2">
                {category === 'data-issue' ? 'What looks wrong?' : 'Your feedback'}
              </label>
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={6}
                required
                maxLength={4000}
                placeholder={activeCat.hint}
                className="w-full px-4 py-3 rounded-xl bg-white border border-light-grey font-body text-body-lg text-deep-navy placeholder:text-cool-grey outline-none focus:border-soft-gold focus:ring-1 focus:ring-soft-gold/30 transition-colors resize-y"
              />
            </div>

            <div>
              <label className="block font-body text-small font-medium text-deep-navy mb-2">
                Email <span className="text-cool-grey font-normal">(optional, only if you want a reply)</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl bg-white border border-light-grey font-body text-body-lg text-deep-navy placeholder:text-cool-grey outline-none focus:border-soft-gold focus:ring-1 focus:ring-soft-gold/30 transition-colors"
              />
            </div>

            {error && <p className="font-body text-small text-destructive">{error}</p>}

            <button
              type="submit"
              disabled={sending || !message.trim()}
              className="inline-flex items-center justify-center px-7 py-3 rounded-full bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
            >
              {sending ? 'Sending…' : 'Send'}
            </button>

            <p className="font-body text-caption text-cool-grey leading-[1.5] pt-2">
              We never collect your IP, never track you, and store nothing beyond this
              message and the email you choose to share. Private by design.
            </p>
          </form>
        </>
      )}
    </div>
  )
}
