import React, { useState } from 'react'
import { useWallet } from '../contexts/WalletContext'

interface DonationLoggerProps {
  ein: string
  orgName: string
  orgOptedInLetters?: boolean
}

export default function DonationLogger({ ein, orgName, orgOptedInLetters = false }: DonationLoggerProps) {
  const { logDonation } = useWallet()
  const [donorName, setDonorName] = useState('')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [notes, setNotes] = useState('')
  const [requestLetter, setRequestLetter] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const canRequestLetter = orgOptedInLetters && parseInt(amount) >= 250

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!amount || !date) {
      setError('Amount and date required')
      return
    }

    const parsedAmount = parseInt(amount)
    if (parsedAmount < 1) {
      setError('Amount must be at least $1')
      return
    }

    setLoading(true)

    try {
      // Log donation to wallet
      logDonation(ein, parsedAmount, date, notes || undefined)

      // If requesting letter, send to nonprofit approval queue
      if (requestLetter && canRequestLetter) {
        const letterRes = await fetch('/api/nonprofit/letter-request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ein,
            amount: parsedAmount,
            date,
            donorName: donorName || 'Anonymous',
          }),
        })
        if (!letterRes.ok) {
          setError('Failed to request letter. Try again.')
          return
        }
      }

      setSuccess(true)
      setDonorName('')
      setAmount('')
      setNotes('')
      setRequestLetter(false)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-md border border-light-grey">
      <h3 className="font-display text-lg italic text-deep-navy mb-4">Log your donation</h3>

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-green-700 text-sm">
          ✓ Donation logged. {requestLetter ? 'Letter request sent!' : 'You can generate a tax receipt anytime.'}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Donor Name */}
        <div>
          <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
            Your name (optional)
          </label>
          <input
            type="text"
            value={donorName}
            onChange={(e) => setDonorName(e.target.value.slice(0, 100))}
            placeholder="Leave blank to remain anonymous"
            maxLength={100}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
          <p className="text-xs text-cool-grey mt-1">Private to {orgName} only</p>
        </div>

        {/* Amount */}
        <div>
          <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
            Amount *
          </label>
          <div className="flex items-center gap-2">
            <span className="text-deep-navy">$</span>
            <input
              type="number"
              min="1"
              max="999999"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0"
              className="flex-1 px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
            />
          </div>
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
            Notes (optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value.slice(0, 200))}
            placeholder="e.g., matched by employer, year-end gift"
            maxLength={200}
            rows={2}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50 resize-none"
          />
          <p className="text-xs text-cool-grey mt-1">{notes.length}/200</p>
        </div>

        {/* Request Letter */}
        {orgOptedInLetters && (
          <div className="bg-soft-cream rounded-lg p-3">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={requestLetter}
                onChange={(e) => setRequestLetter(e.target.checked)}
                disabled={!canRequestLetter}
                className="mt-1"
              />
              <span className="font-body text-sm text-deep-navy">
                {canRequestLetter ? (
                  <>Request a tax letter for this donation</>
                ) : (
                  <>Donations of $250+ can request a tax letter</>
                )}
              </span>
            </label>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !amount || !date}
          className="w-full py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-sm font-semibold hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? 'Logging...' : 'Log donation'}
        </button>
      </form>
    </div>
  )
}
