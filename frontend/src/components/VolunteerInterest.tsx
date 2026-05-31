import { useState } from 'react'

// Privacy-preserving volunteer interest. The user composes a short intro and sends it
// from their OWN device (their email app, or by pasting into the org's page). Daanaa
// stores no contact list, so there is nothing to harvest or spam. The user controls
// per-send whether to reveal a first name + age range or stay anonymous.

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

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-deep-navy/40 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-card" onClick={e => e.stopPropagation()}>
        <h3 className="font-display text-[19px] text-deep-navy">Volunteer with {orgName}</h3>
        <p className="mt-1 font-body text-[13px] text-cool-grey">
          You send this from your own device. Daanaa never stores your contact info, so you
          will not get spam from us or a stored list.
        </p>

        {/* Anonymous vs named */}
        <div className="mt-4 flex rounded-lg border border-light-grey p-1 text-[13px] font-medium">
          <button
            onClick={() => setAnonymous(true)}
            className={`flex-1 rounded-md py-1.5 transition-colors ${anonymous ? 'bg-deep-navy text-warm-cream' : 'text-cool-grey'}`}
          >Stay anonymous</button>
          <button
            onClick={() => setAnonymous(false)}
            className={`flex-1 rounded-md py-1.5 transition-colors ${!anonymous ? 'bg-deep-navy text-warm-cream' : 'text-cool-grey'}`}
          >Share my first name</button>
        </div>

        {!anonymous && (
          <input
            value={firstName}
            onChange={e => setFirstName(e.target.value)}
            placeholder="First name"
            className="mt-2 w-full rounded-lg border border-light-grey px-3 py-2 font-body text-[14px]"
          />
        )}

        <div className="mt-2">
          <label className="font-body text-[12px] text-cool-grey">Age range (optional, shown to the org)</label>
          <select
            value={ageRange}
            onChange={e => setAgeRange(e.target.value)}
            className="mt-1 w-full rounded-lg border border-light-grey px-3 py-2 font-body text-[14px]"
          >
            <option value="">Prefer not to say</option>
            {AGE_RANGES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>

        {/* Preview of exactly what the org sees */}
        <div className="mt-3 rounded-lg bg-cream/50 border border-light-grey p-3 font-body text-[12px] text-cool-grey whitespace-pre-wrap">
          {message}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {contactEmail && (
            <button onClick={sendByEmail} className="rounded-full bg-soft-gold px-4 py-2 font-body text-[13px] font-semibold text-deep-navy hover:bg-bright-gold transition-colors">
              Send by email
            </button>
          )}
          {website && (
            <button onClick={copyAndOpenSite} className="rounded-full border border-deep-navy/20 px-4 py-2 font-body text-[13px] font-medium text-deep-navy hover:bg-deep-navy/5 transition-colors">
              {copied ? 'Copied — opening their site' : "Copy intro & open their site"}
            </button>
          )}
          <button onClick={onClose} className="rounded-full px-4 py-2 font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors">
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
