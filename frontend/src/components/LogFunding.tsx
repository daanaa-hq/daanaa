import { useState } from 'react'
import { logFunding } from '../data/api'
import { useAuth } from '../contexts/AuthContext'

interface LogFundingProps {
  onSuccess?: () => void
}

export default function LogFunding({ onSuccess }: LogFundingProps) {
  const { getIdToken } = useAuth()
  const [ein, setEin] = useState('')
  const [nonprofitName, setNonprofitName] = useState('')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const token = await getIdToken()
      if (!token) {
        setError('Unable to get authentication token')
        return
      }

      const fundingAmount = parseFloat(amount)
      if (!fundingAmount || fundingAmount <= 0) {
        setError('Please enter a valid amount')
        return
      }

      if (!ein.trim() || !nonprofitName.trim()) {
        setError('Please enter EIN and nonprofit name')
        return
      }

      await logFunding(token, ein.trim(), nonprofitName.trim(), fundingAmount, date)

      // Reset form
      setEin('')
      setNonprofitName('')
      setAmount('')
      setDate(new Date().toISOString().split('T')[0])

      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to log funding')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-deep-navy mb-1">
          Organization EIN
        </label>
        <input
          type="text"
          value={ein}
          onChange={(e) => setEin(e.target.value.replace(/\D/g, '').slice(0, 9))}
          placeholder="e.g., 123456789"
          className="w-full px-3 py-2 border border-light-grey rounded-lg focus:outline-none focus:border-soft-gold"
          maxLength={9}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-deep-navy mb-1">
          Organization Name
        </label>
        <input
          type="text"
          value={nonprofitName}
          onChange={(e) => setNonprofitName(e.target.value)}
          placeholder="e.g., Local Food Bank"
          className="w-full px-3 py-2 border border-light-grey rounded-lg focus:outline-none focus:border-soft-gold"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-deep-navy mb-1">
            Amount ($)
          </label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            step="0.01"
            min="0"
            className="w-full px-3 py-2 border border-light-grey rounded-lg focus:outline-none focus:border-soft-gold"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-deep-navy mb-1">
            Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full px-3 py-2 border border-light-grey rounded-lg focus:outline-none focus:border-soft-gold"
            required
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Logging...' : 'Log Gift'}
      </button>
    </form>
  )
}
