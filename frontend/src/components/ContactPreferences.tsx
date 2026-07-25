import { useState } from 'react'

interface ContactPreferencesProps {
  ein: string
  pin: string
  onSuccess?: () => void
}

export default function ContactPreferences({ ein, pin, onSuccess }: ContactPreferencesProps) {
  const [preference, setPreference] = useState<'unified' | 'separate'>('unified')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [contactName, setContactName] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')

  const [volunteerName, setVolunteerName] = useState('')
  const [volunteerEmail, setVolunteerEmail] = useState('')
  const [volunteerPhone, setVolunteerPhone] = useState('')

  const [donorName, setDonorName] = useState('')
  const [donorEmail, setDonorEmail] = useState('')
  const [donorPhone, setDonorPhone] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const data = {
        ein,
        pin,
        contact_preference: preference,
      }

      if (preference === 'unified') {
        Object.assign(data, {
          contact_name: contactName.trim(),
          contact_email: contactEmail.trim(),
          contact_phone: contactPhone.trim(),
        })
      } else {
        Object.assign(data, {
          volunteer_contact_name: volunteerName.trim(),
          volunteer_contact_email: volunteerEmail.trim(),
          volunteer_contact_phone: volunteerPhone.trim(),
          donor_contact_name: donorName.trim(),
          donor_contact_email: donorEmail.trim(),
          donor_contact_phone: donorPhone.trim(),
        })
      }

      const response = await fetch('/api/claim/contacts', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const body = await response.json()
        throw new Error(body.error || 'Failed to update contact preferences')
      }

      setSuccess(true)
      setTimeout(() => {
        setSuccess(false)
        onSuccess?.()
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-green-800 font-medium">✓ Contact preferences saved</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-lg font-display text-deep-navy mb-3">Contact Preferences</h3>
        <p className="text-sm text-cool-grey mb-4">
          Tell us how volunteers and donors should reach you.
        </p>
      </div>

      {/* Contact Preference Toggle */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-deep-navy">Contact Type</label>

        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="preference"
              value="unified"
              checked={preference === 'unified'}
              onChange={(e) => setPreference(e.target.value as 'unified' | 'separate')}
              className="w-4 h-4"
            />
            <span className="text-sm text-deep-navy">
              <span className="font-medium">Same Contact</span>
              <p className="text-xs text-cool-grey">Use one contact for all</p>
            </span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="preference"
              value="separate"
              checked={preference === 'separate'}
              onChange={(e) => setPreference(e.target.value as 'unified' | 'separate')}
              className="w-4 h-4"
            />
            <span className="text-sm text-deep-navy">
              <span className="font-medium">Different Contacts</span>
              <p className="text-xs text-cool-grey">Separate volunteer & donor contacts</p>
            </span>
          </label>
        </div>
      </div>

      {/* Unified Contact Fields */}
      {preference === 'unified' && (
        <div className="bg-warm-cream rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-deep-navy mb-2">
              Contact Name
            </label>
            <input
              type="text"
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              placeholder="e.g., Jane Doe"
              className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-deep-navy mb-2">
              Contact Email
            </label>
            <input
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              placeholder="contact@org.org"
              className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-deep-navy mb-2">
              Contact Phone
            </label>
            <input
              type="tel"
              value={contactPhone}
              onChange={(e) => setContactPhone(e.target.value)}
              placeholder="(555) 123-4567"
              className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
            />
          </div>
        </div>
      )}

      {/* Volunteer & Donor Contact Fields */}
      {preference === 'separate' && (
        <div className="space-y-4">
          {/* Volunteer Contacts */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
            <h4 className="font-medium text-deep-navy">Volunteer Contact</h4>

            <div>
              <label className="block text-sm font-medium text-deep-navy mb-2">
                Name
              </label>
              <input
                type="text"
                value={volunteerName}
                onChange={(e) => setVolunteerName(e.target.value)}
                placeholder="e.g., John Smith"
                className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-deep-navy mb-2">
                Email
              </label>
              <input
                type="email"
                value={volunteerEmail}
                onChange={(e) => setVolunteerEmail(e.target.value)}
                placeholder="volunteer@org.org"
                className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-deep-navy mb-2">
                Phone
              </label>
              <input
                type="tel"
                value={volunteerPhone}
                onChange={(e) => setVolunteerPhone(e.target.value)}
                placeholder="(555) 123-4567"
                className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
              />
            </div>
          </div>

          {/* Donor Contacts */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
            <h4 className="font-medium text-deep-navy">Donor Contact</h4>

            <div>
              <label className="block text-sm font-medium text-deep-navy mb-2">
                Name
              </label>
              <input
                type="text"
                value={donorName}
                onChange={(e) => setDonorName(e.target.value)}
                placeholder="e.g., Sarah Johnson"
                className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-deep-navy mb-2">
                Email
              </label>
              <input
                type="email"
                value={donorEmail}
                onChange={(e) => setDonorEmail(e.target.value)}
                placeholder="donors@org.org"
                className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-deep-navy mb-2">
                Phone
              </label>
              <input
                type="tel"
                value={donorPhone}
                onChange={(e) => setDonorPhone(e.target.value)}
                placeholder="(555) 987-6543"
                className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
              />
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-3">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Saving...' : 'Save Contact Preferences'}
      </button>
    </form>
  )
}
