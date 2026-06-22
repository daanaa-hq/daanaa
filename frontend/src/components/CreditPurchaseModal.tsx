import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { CreditPurchaseSchema } from '../lib/schemas'

interface CreditPurchaseModalProps {
  nonprofitEin: string
  currentBalance: number
  onClose: () => void
  onSuccess: (creditsAdded: number) => void
}

export default function CreditPurchaseModal({
  nonprofitEin,
  currentBalance,
  onClose,
  onSuccess,
}: CreditPurchaseModalProps) {
  const { user } = useAuth()
  const [quantity, setQuantity] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const PRICE_PER_CREDIT = 299 // $2.99 in cents
  const totalPrice = (quantity * PRICE_PER_CREDIT) / 100

  const handlePurchase = async () => {
    if (!user) {
      setError('Sign in to purchase credits')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const token = await user.getIdToken()
      const res = await fetch('/api/nonprofit/letter-credits/purchase', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${nonprofitEin}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quantity,
          payment_method: 'stripe',
        }),
      })

      if (!res.ok) throw new Error('Purchase failed')
      const data = await res.json()
      onSuccess(quantity)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full">
        <h2 className="font-display text-2xl text-deep-navy mb-4">Purchase Letter Credits</h2>

        <div className="bg-soft-cream rounded-lg p-4 mb-6">
          <p className="text-sm text-cool-grey mb-2">Current Balance</p>
          <p className="font-display text-3xl text-deep-navy">{currentBalance}</p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-semibold text-deep-navy mb-2">
            Number of Credits
          </label>
          <input
            type="number"
            min="1"
            max="100"
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          />
          <p className="text-xs text-cool-grey mt-2">
            ${PRICE_PER_CREDIT / 100} per credit
          </p>
        </div>

        <div className="bg-soft-gold/10 rounded-lg p-4 mb-6">
          <p className="text-sm text-cool-grey mb-2">Total Price</p>
          <p className="font-semibold text-xl text-deep-navy">${totalPrice.toFixed(2)}</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-light-grey rounded-lg font-semibold text-deep-navy hover:bg-soft-cream transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handlePurchase}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-soft-gold text-deep-navy rounded-lg font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Purchase'}
          </button>
        </div>
      </div>
    </div>
  )
}
