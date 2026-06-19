import { useState } from 'react'

// Privacy-preserving volunteer interest. The user composes a short intro and sends it
// from their OWN device — Daanaa stores no contact list, so there is nothing to harvest or spam.

const AGE_RANGES = ['under 18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+'] as const

export default function VolunteerInterest({
  orgName,
  website,
  contactEmail,
  onClose,
}: {
  orgName: string
  website?: string | null
  contactEmail?: string | null
  onClose: () => void
}) {
  const [anonymous, setAnonymous] = useState(true)
  const [firstName, setFirstName] = useState('')
  const [ageRange, setAgeRange] = useState<string>('')
  const [copied, setCopied] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const who = anonymous
    ? `An interested supporter${ageRange ? ` (age ${ageRange})` : ''}`
    : `${firstName.trim() || 'A supporter'}${ageRange ? `, age ${ageRange}` : ''}`

  const message =
    `Hi ${orgName}, I found you on Daanaa and I'd like to help out as a volunteer. ` +
    `Please let me know how to get involved.\n\n— ${who}`

  const sendByEmail = () => {
    const subject = encodeURIComponent(`Volunteer interest — via Daanaa`)
    const body = encodeURIComponent(message)
    window.location.href = `mailto:${contactEmail}?subject=${subject}&body=${body}`
  }

  const copyAndOpenSite = async () => {
    try { await navigator.clipboard.writeText(message); setCopied(true) } catch { /* ignore */ }
    if (website) window.open(website, '_blank', 'noopener')
  }

  const hasAction = contactEmail || website

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-deep-navy/50 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-[420px] rounded-2xl bg-white shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-warm-cream px-6 pt-5 pb-4 border-b border-light-grey">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-body text-[11px] font-semibold text-soft-gold uppercase tracking-widest mb-0.5">Volunteer interest</p>
              <h3 className="font-display text-[20px] text-deep-navy leading-snug">{orgName}</h3>
            </div>
            <button
              onClick={onClose}
              className="shrink-0 mt-0.5 p-1.5 rounded-lg text-cool-grey hover:text-deep-navy hover:bg-light-grey/40 transition-colors"
              aria-label="Close"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="mt-2 font-body text-[12px] text-cool-grey leading-relaxed">
            You send this from your own device. Daanaa never stores your contact info.
          </p>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          {/* Anonymous vs named toggle */}
          <div>
            <p className="font-body text-[12px] font-medium text-deep-navy mb-2">How do you want to sign it?</p>
            <div className="flex rounded-xl border border-light-grey overflow-hidden text-[13px] font-medium">
              <button
                onClick={() => setAnonymous(true)}
                className={`flex-1 py-2 transition-colors ${anonymous ? 'bg-deep-navy text-warm-cream' : 'text-cool-grey hover:bg-warm-cream/60'}`}
              >
                Stay anonymous
              </button>
              <button
                onClick={() => setAnonymous(false)}
                className={`flex-1 py-2 transition-colors ${!anonymous ? 'bg-deep-navy text-warm-cream' : 'text-cool-grey hover:bg-warm-cream/60'}`}
              >
                Use my first name
              </button>
            </div>
          </div>

          {!anonymous && (
            <input
              value={firstName}
              onChange={e => setFirstName(e.target.value)}
              placeholder="First name"
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-[14px] text-deep-navy placeholder:text-cool-grey/50 focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
            />
          )}

          <div>
            <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">Age range <span className="font-normal text-cool-grey">(optional)</span></label>
            <select
              value={ageRange}
              onChange={e => setAgeRange(e.target.value)}
              className="w-full px-4 py-2.5 border border-light-grey rounded-xl font-body text-[14px] text-deep-navy bg-white focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
            >
              <option value="">Prefer not to say</option>
              {AGE_RANGES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          {/* Message preview (collapsible) */}
          <div>
            <button
              onClick={() => setShowPreview(v => !v)}
              className="flex items-center gap-1.5 font-body text-[12px] text-soft-gold hover:text-bright-gold transition-colors"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d={showPreview ? 'M18 15l-6-6-6 6' : 'M6 9l6 6 6-6'} />
              </svg>
              {showPreview ? 'Hide' : 'Preview'} message
            </button>
            {showPreview && (
              <div className="mt-2 rounded-xl bg-warm-cream border border-light-grey px-4 py-3 font-body text-[12px] text-cool-grey whitespace-pre-wrap leading-relaxed">
                {message}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 pb-6 space-y-2.5">
          {contactEmail && (
            <button
              onClick={sendByEmail}
              className="w-full py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors flex items-center justify-center gap-2"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
              </svg>
              Send by email
            </button>
          )}
          {website && (
            <button
              onClick={copyAndOpenSite}
              className="w-full py-3 rounded-xl border border-deep-navy/20 text-deep-navy font-body text-[14px] font-medium hover:bg-warm-cream transition-colors flex items-center justify-center gap-2"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              {copied ? 'Message copied — opening their site' : 'Copy message and open their website'}
            </button>
          )}
          {!hasAction && (
            <p className="text-center font-body text-[13px] text-cool-grey py-2">
              This organization has not shared a contact email or website yet.
            </p>
          )}
          <button
            onClick={onClose}
            className="w-full py-2.5 font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
