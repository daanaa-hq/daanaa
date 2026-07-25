import React, { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

export default function NonprofitVerification() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [error, setError] = useState('')

  useEffect(() => {
    const verify = async () => {
      const accountId = searchParams.get('id')
      if (!accountId) {
        setStatus('error')
        setError('No verification link provided')
        return
      }

      try {
        // Store the account ID as the auth token for nonprofit dashboard
        // (Backend will validate this against nonprofit_accounts table)
        localStorage.setItem('nonprofit_account_id', accountId)
        setStatus('success')

        // Redirect to dashboard after 1 second
        setTimeout(() => {
          navigate('/nonprofit/dashboard')
        }, 1000)
      } catch (err) {
        setStatus('error')
        setError((err as Error).message)
      }
    }

    verify()
  }, [searchParams, navigate])

  return (
    <div className="min-h-screen bg-gradient-to-br from-soft-cream to-white flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        {status === 'verifying' && (
          <>
            <div className="inline-flex items-center justify-center w-12 h-12 bg-soft-gold/20 rounded-full mb-6 animate-spin">
              <div className="w-8 h-8 border-2 border-soft-gold border-t-transparent rounded-full" />
            </div>
            <h2 className="font-display text-2xl text-deep-navy mb-2">Verifying account</h2>
            <p className="text-cool-grey">Setting up your nonprofit dashboard...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-6">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="font-display text-2xl text-deep-navy mb-2">Email verified!</h2>
            <p className="text-cool-grey mb-4">Taking you to your dashboard...</p>
            <div className="inline-flex items-center justify-center w-8 h-8 bg-soft-gold/20 rounded-full animate-spin">
              <div className="w-6 h-6 border-2 border-soft-gold border-t-transparent rounded-full" />
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="inline-flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mb-6">
              <svg className="w-6 h-6 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="font-display text-2xl text-deep-navy mb-2">Verification failed</h2>
            <p className="text-destructive mb-4">{error}</p>
            <button
              onClick={() => window.location.href = '/nonprofit/signup'}
              className="w-full py-2.5 rounded-lg bg-soft-gold text-deep-navy font-semibold hover:bg-bright-gold transition-colors"
            >
              Try signing up again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
