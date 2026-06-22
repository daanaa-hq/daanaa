import React, { useState } from 'react'
import { useWallet } from '../contexts/WalletContext'

interface VolunteerLoggerProps {
  ein: string
  orgName: string
}

export default function VolunteerLogger({ ein, orgName }: VolunteerLoggerProps) {
  const { logVolunteerHours } = useWallet()
  const [hours, setHours] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [notes, setNotes] = useState('')
  const [helpedDaanaa, setHelpedDaanaa] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!hours || !date) {
      setError('Hours and date required')
      return
    }

    const parsedHours = parseFloat(hours)
    if (parsedHours < 0.25) {
      setError('Hours must be at least 0.25')
      return
    }

    setLoading(true)

    try {
      logVolunteerHours(ein, parsedHours, date, notes || undefined, helpedDaanaa)

      setSuccess(true)
      setHours('')
      setNotes('')
      setHelpedDaanaa(false)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-md border border-light-grey">
      <h3 className="font-display text-lg italic text-deep-navy mb-4">Log your volunteer hours</h3>

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-green-700 text-sm">
          ✓ Hours logged for {orgName}. Your time is valuable!
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Hours */}
        <div>
          <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
            Hours contributed *
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0.25"
              step="0.25"
              max="24"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              placeholder="0.0"
              className="flex-1 px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
            />
            <span className="text-cool-grey text-sm">hours</span>
          </div>
          <p className="text-xs text-cool-grey mt-1">Minimum 0.25 hours (15 minutes)</p>
        </div>

        {/* Date */}
        <div>
          <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
            Date *
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
            What did you help with? (optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value.slice(0, 200))}
            placeholder="e.g., led a workshop, sorted donations, mentoring"
            maxLength={200}
            rows={2}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50 resize-none"
          />
          <p className="text-xs text-cool-grey mt-1">{notes.length}/200</p>
        </div>

        {/* Help Daanaa Measure Impact */}
        <div className="bg-soft-gold/8 border border-soft-gold/30 rounded-lg p-3">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={helpedDaanaa}
              onChange={(e) => setHelpedDaanaa(e.target.checked)}
              disabled={helpedDaanaa}
              className="mt-1"
            />
            <div className="flex-1">
              <span className="font-body text-sm font-semibold text-deep-navy">
                {helpedDaanaa ? '✓ Daanaa helped' : 'Help Daanaa measure our impact'}
              </span>
              <p className="font-body text-xs text-cool-grey mt-1">
                {helpedDaanaa
                  ? 'Your volunteer hours are helping us track our community impact (locked)'
                  : 'Include these hours in our monthly impact report'}
              </p>
            </div>
          </label>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !hours || !date}
          className="w-full py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-sm font-semibold hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? 'Logging...' : 'Log hours'}
        </button>
      </form>
    </div>
  )
}
