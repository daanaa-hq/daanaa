import { useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'

const PARTNER_TYPES = [
  'Payment processing',
  'Services for nonprofits',
  'Community foundation or network',
  'Other',
]

export default function Partners() {
  usePageMeta('Partner With Us', 'Daanaa connects verified nonprofits with partners who serve them. If you serve nonprofits, we should talk.')
  const [orgName, setOrgName] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [ptype, setPtype] = useState(PARTNER_TYPES[0])
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSending(true)
    try {
      const res = await fetch('/api/partner/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          org_name: orgName.trim(),
          name: name.trim(),
          email: email.trim(),
          partner_type: ptype,
          message: message.trim(),
        }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Something went wrong. Please try again.')
        setSending(false)
        return
      }
      setSent(true)
    } catch {
      setError('Could not reach the server. You can also email us at partners@daanaa.org.')
      setSending(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      {/* Hero */}
      <div className="bg-deep-navy pt-[108px] pb-16 px-6">
        <div className="max-w-[760px] mx-auto">
          <p className="font-body text-[12px] font-medium tracking-[0.12em] text-soft-gold uppercase mb-4">
            For Partners
          </p>
          <h1 className="font-display italic text-warm-cream leading-[1.1] mb-5" style={{ fontSize: 'clamp(30px, 4.5vw, 48px)' }}>
            A rising tide raises all boats.
          </h1>
          <p className="font-body text-[17px] text-warm-cream/80 leading-[1.7] max-w-[620px]">
            Daanaa lists every U.S. nonprofit the IRS recognizes, more than two million
            organizations. Most of them run on almost no infrastructure: the everyday
            tools, services, and local support that larger organizations take for granted.
            We connect verified organizations with partners who can change that, starting
            in their own communities. If you serve nonprofits, we should talk.
          </p>
        </div>
      </div>

      <div className="max-w-[760px] mx-auto px-6 py-14">
        {/* How partnership works */}
        <div className="grid gap-4 mb-12">
          {[
            {
              title: 'What we bring',
              body: 'A directory of two million organizations and a claim process that verifies each leader by phone before anything goes live. When an organization asks us for help, we know who they are, and we introduce them to partners at the exact moment of need.',
            },
            {
              title: 'What we ask',
              body: 'The best possible terms for small nonprofits. Our comparisons are written in plain language and sorted by what an organization actually pays. Placement cannot be bought. It is earned by terms, and we say so publicly.',
            },
            {
              title: 'What we never do',
              body: 'We never handle donor money, never sell or share our data, and never let a commercial relationship touch how any organization is scored, ranked, or shown.',
            },
          ].map(({ title, body }) => (
            <div key={title} className="bg-white rounded-2xl border border-light-cream p-7">
              <h2 className="font-body text-[15px] font-semibold text-deep-navy mb-2">{title}</h2>
              <p className="font-body text-[15px] text-cool-grey leading-[1.7]">{body}</p>
            </div>
          ))}
        </div>

        {/* Contact form */}
        <div className="bg-white rounded-2xl shadow-sm border border-light-cream p-8">
          {sent ? (
            <div className="text-center py-6">
              <div className="w-14 h-14 rounded-full bg-soft-gold text-deep-navy mx-auto mb-4 flex items-center justify-center text-xl font-bold">✓</div>
              <h2 className="font-display italic text-[24px] text-deep-navy mb-2">Thank you</h2>
              <p className="font-body text-[15px] text-cool-grey">
                We read every inquiry and reply from partners@daanaa.org.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <h2 className="font-display italic text-[24px] text-deep-navy mb-1">Start the conversation</h2>
              <p className="font-body text-[14px] text-cool-grey mb-6">
                Tell us who you are and how you serve nonprofits.
              </p>
              {error && (
                <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl">
                  <p className="font-body text-[14px] text-red-700">{error}</p>
                </div>
              )}
              <div className="grid sm:grid-cols-2 gap-4 mb-4">
                <label className="block">
                  <span className="block font-body text-[13px] font-medium text-deep-navy mb-1.5">Your name</span>
                  <input
                    type="text" value={name} onChange={e => setName(e.target.value)} required
                    className="w-full px-4 py-2.5 border border-light-cream rounded-xl font-body text-[14px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold"
                  />
                </label>
                <label className="block">
                  <span className="block font-body text-[13px] font-medium text-deep-navy mb-1.5">Company or organization</span>
                  <input
                    type="text" value={orgName} onChange={e => setOrgName(e.target.value)}
                    className="w-full px-4 py-2.5 border border-light-cream rounded-xl font-body text-[14px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold"
                  />
                </label>
              </div>
              <div className="grid sm:grid-cols-2 gap-4 mb-4">
                <label className="block">
                  <span className="block font-body text-[13px] font-medium text-deep-navy mb-1.5">Email</span>
                  <input
                    type="email" value={email} onChange={e => setEmail(e.target.value)} required
                    className="w-full px-4 py-2.5 border border-light-cream rounded-xl font-body text-[14px] text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold"
                  />
                </label>
                <label className="block">
                  <span className="block font-body text-[13px] font-medium text-deep-navy mb-1.5">How you serve nonprofits</span>
                  <select
                    value={ptype} onChange={e => setPtype(e.target.value)}
                    className="w-full px-4 py-2.5 border border-light-cream rounded-xl font-body text-[14px] text-deep-navy bg-white focus:outline-none focus:ring-2 focus:ring-soft-gold"
                  >
                    {PARTNER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </label>
              </div>
              <label className="block mb-6">
                <span className="block font-body text-[13px] font-medium text-deep-navy mb-1.5">Message</span>
                <textarea
                  value={message} onChange={e => setMessage(e.target.value)} required rows={5} maxLength={5000}
                  placeholder="What you offer, and what working together could look like."
                  className="w-full px-4 py-3 border border-light-cream rounded-xl font-body text-[14px] text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-y"
                />
              </label>
              <button
                type="submit" disabled={sending}
                className="w-full sm:w-auto px-8 py-3 bg-soft-gold text-deep-navy font-body text-[15px] font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors"
              >
                {sending ? 'Sending…' : 'Send inquiry'}
              </button>
              <p className="mt-4 font-body text-[13px] text-muted-cream">
                Prefer email? Write to{' '}
                <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">partners@daanaa.org</a>
              </p>
            </form>
          )}
        </div>

        <p className="mt-8 font-body text-[13px] text-cool-grey leading-[1.7] text-center max-w-[560px] mx-auto">
          Daanaa operates under a published stewardship commitment. Independence is one of
          its principles, and every partnership lives inside it. Read it at{' '}
          <a href="/principles" className="text-soft-gold hover:underline">daanaa.org/principles</a>.
        </p>
      </div>
    </div>
  )
}
