import { useState } from 'react'

interface EventInterestModalProps {
  eventId: string
  eventTitle: string
  orgEin: string
  orgName: string
  onClose: () => void
  onSuccess: () => void
}

export function EventInterestModal({
  eventId,
  eventTitle,
  orgEin,
  orgName,
  onClose,
  onSuccess,
}: EventInterestModalProps) {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`/api/volunteer-interest/${orgEin}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, event_id: eventId, event_title: eventTitle }),
      })

      if (!response.ok) throw new Error('Failed to submit interest')

      onSuccess()
      onClose()
    } catch (err) {
      setError('Error submitting interest. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-lg">
        <h2 className="font-display text-xl text-deep-navy mb-2">Interested in this opportunity?</h2>
        <p className="font-body text-sm text-cool-grey mb-4">{eventTitle} — {orgName}</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-body text-xs font-medium text-deep-navy mb-1.5">
              Your email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-3 py-2 rounded-lg border border-light-cream font-body text-sm focus:outline-none focus:border-soft-gold/60"
              disabled={loading}
            />
          </div>

          {error && <p className="font-body text-xs text-red-600">{error}</p>}

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg border border-light-cream font-body text-sm text-cool-grey hover:bg-light-cream transition-colors disabled:opacity-60"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-soft-gold text-deep-navy rounded-lg font-body text-sm font-semibold hover:bg-bright-gold transition-colors disabled:opacity-60"
              disabled={loading || !email.trim()}
            >
              {loading ? 'Sending...' : 'Express Interest'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
