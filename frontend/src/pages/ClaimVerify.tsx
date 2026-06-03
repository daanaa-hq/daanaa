import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { formatEINInput } from '../data/organizations'

export default function ClaimVerify() {
  usePageMeta('Verify your claim', 'Enter your EIN and PIN to verify your organization claim on Daanaa.')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [ein, setEin] = useState(formatEINInput(searchParams.get('ein') || ''))
  const [pin, setPin] = useState(searchParams.get('pin') || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Auto-submit if both ein and pin came in via QR code URL
  useEffect(() => {
    const qrEin = searchParams.get('ein')
    const qrPin = searchParams.get('pin')
    if (qrEin && qrPin) {
      handleVerify(qrEin.replace(/\D/g, ''), qrPin.replace(/\D/g, ''))
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleVerify(einVal = ein, pinVal = pin) {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch('/api/claim/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein: einVal.replace(/\D/g, ''), pin: pinVal.replace(/\D/g, '') }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Verification failed. Please check your EIN and PIN.')
        setLoading(false)
        return
      }
      // Pass verified data to editor via navigation state
      navigate('/claim/edit', {
        state: {
          ein: einVal.replace(/\D/g, ''),
          pin: pinVal.replace(/\D/g, ''),
          org_name: body.org_name,
          current_mission: body.current_mission,
          current_donate_url: body.current_donate_url,
          irs_address: body.irs_address,
        },
      })
    } catch {
      setError('Could not reach the server. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
      <div className="max-w-[520px] mx-auto px-6 py-16">
        <div className="flex items-center gap-2 mb-8">
          <Link to="/" className="font-body text-[12px] text-cool-grey hover:text-deep-navy transition-colors">Home</Link>
          <span className="text-cool-grey/40">/</span>
          <span className="font-body text-[12px] text-cool-grey">Verify claim</span>
        </div>

        <h1 className="font-display italic text-deep-navy text-[32px] leading-[1.1] mb-3">
          Enter your verification PIN
        </h1>
        <p className="font-body text-[15px] text-cool-grey leading-[1.6] mb-8">
          Check the letter we mailed to your organization's IRS-registered address.
          Enter the EIN and 6-digit PIN from the letter, or scan the QR code directly.
        </p>

        <form
          onSubmit={e => { e.preventDefault(); handleVerify() }}
          className="space-y-4"
        >
          <div>
            <label className="block font-body text-[12px] text-cool-grey mb-1.5">
              Organization EIN <span className="text-soft-gold">*</span>
            </label>
            <input
              type="text"
              required
              value={ein}
              onChange={e => setEin(formatEINInput(e.target.value))}
              placeholder="12-3456789"
              className="w-full h-[48px] bg-white border border-light-grey text-deep-navy px-4 rounded-xl font-body text-[15px] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
            />
          </div>
          <div>
            <label className="block font-body text-[12px] text-cool-grey mb-1.5">
              6-digit PIN from your letter <span className="text-soft-gold">*</span>
            </label>
            <input
              type="text"
              inputMode="numeric"
              required
              value={pin}
              onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full h-[48px] bg-white border border-light-grey text-deep-navy px-4 rounded-xl font-body text-[20px] font-mono tracking-[0.3em] outline-none focus:border-soft-gold transition-colors placeholder:text-cool-grey"
            />
          </div>

          {error && (
            <p className="font-body text-[13px] text-red-600 leading-[1.5]">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || ein.replace(/\D/g, '').length < 9 || pin.length < 6}
            className="w-full h-[48px] bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-full hover:bg-bright-gold transition-colors disabled:opacity-50"
          >
            {loading ? 'Verifying…' : 'Verify PIN'}
          </button>
        </form>

        <p className="mt-6 font-body text-[12px] text-cool-grey leading-[1.5]">
          Don't have your letter yet? It usually arrives in 3–5 business days.{' '}
          <Link to="/feedback?type=org" className="underline underline-offset-2 hover:text-deep-navy transition-colors">
            Contact us
          </Link>{' '}
          if you need help.
        </p>
      </div>
    </div>
  )
}
