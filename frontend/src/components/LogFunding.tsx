import { useState } from 'react'
import { logFunding } from '../data/api'
import { useAuth } from '../contexts/AuthContext'

interface LogFundingProps {
  onSuccess?: () => void
}

export default function LogFunding({ onSuccess }: LogFundingProps) {
  const { user, getIdToken, signInWithGoogle } = useAuth()
  const [ein, setEin] = useState('')
  const [nonprofitName, setNonprofitName] = useState('')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Require login before saving
    if (!user) {
      setError('Please sign in with Google to save your giving history')
      return
    }

    setLoading(true)

    try {
      const token = await getIdToken()
      if (!token) {
        setError('Unable to get authentication token. Please try signing in again.')
        setLoading(false)
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
        <div className={`rounded-lg p-4 ${
          error.includes('sign in')
            ? 'bg-blue-50 border border-blue-200'
            : 'bg-red-50 border border-red-200'
        }`}>
          <p className={error.includes('sign in') ? 'text-blue-700 text-sm' : 'text-red-700 text-sm'}>
            {error}
          </p>
          {error.includes('sign in') && (
            <button
              type="button"
              onClick={() => signInWithGoogle()}
              className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#fff"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#fff"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#fff"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#fff"/>
              </svg>
              Sign in with Google
            </button>
          )}
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
