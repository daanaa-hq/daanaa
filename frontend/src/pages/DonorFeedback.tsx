import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { API_BASE } from '../data/api'

export default function DonorFeedback() {
  usePageMeta(
    'Help Us Improve | Daanaa',
    'Give us feedback about your experience on Daanaa.'
  )

  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const ein = searchParams.get('ein')
  const orgName = searchParams.get('org')

  const [step, setStep] = useState<'helpful' | 'details' | 'thanks'>(ein ? 'helpful' : 'thanks')
  const [helpful, setHelpful] = useState<'yes' | 'no' | null>(null)
  const [category, setCategory] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleHelpful = async (isHelpful: boolean) => {
    setHelpful(isHelpful ? 'yes' : 'no')
    if (isHelpful) {
      // Submit immediately for positive feedback
      submitFeedback(isHelpful ? 'yes' : 'no', null, '')
    } else {
      setStep('details')
    }
  }

  const submitFeedback = async (helpfulValue: string, catValue: string | null, msg: string) => {
    if (!ein) {
      setStep('thanks')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/api/public/nonprofit/${ein}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          was_helpful: helpfulValue === 'yes',
          feedback_category: catValue,
          message: msg.trim()
        })
      })

      if (!res.ok) throw new Error('Failed to submit feedback')
      setStep('thanks')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit')
    } finally {
      setSubmitting(false)
    }
  }

  if (step === 'thanks') {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center px-6">
        <div className="max-w-md w-full text-center bg-white p-8 rounded-2xl shadow-sm">
          <div className="text-5xl mb-4">💚</div>
          <h1 className="font-display text-2xl text-deep-navy mb-2">Thank You!</h1>
          <p className="font-body text-[14px] text-cool-grey mb-6">
            Your feedback helps us improve Daanaa and better serve nonprofits and donors.
          </p>
          <button
            onClick={() => navigate(-1)}
            className="w-full py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition"
          >
            Back
          </button>
        </div>
      </div>
    )
  }

  if (step === 'helpful') {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center px-6">
        <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-sm">
          <h1 className="font-display text-2xl text-deep-navy mb-2">Was This Helpful?</h1>
          {orgName && (
            <p className="font-body text-[14px] text-cool-grey mb-6">
              Did the information about <strong>{orgName}</strong> help you make a decision?
            </p>
          )}
          {!orgName && (
            <p className="font-body text-[14px] text-cool-grey mb-6">
              Was your experience on Daanaa helpful?
            </p>
          )}

          <div className="space-y-3">
            <button
              onClick={() => handleHelpful(true)}
              className="w-full p-4 rounded-lg border-2 border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-deep-navy font-body text-[14px] font-semibold transition"
            >
              👍 Yes, very helpful
            </button>
            <button
              onClick={() => handleHelpful(false)}
              className="w-full p-4 rounded-lg border-2 border-amber-300 bg-amber-50 hover:bg-amber-100 text-deep-navy font-body text-[14px] font-semibold transition"
            >
              👎 Not really
            </button>
          </div>

          <p className="font-body text-[11px] text-cool-grey text-center mt-6">
            Your feedback is anonymous and helps us improve.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream flex items-center justify-center px-6">
      <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-sm">
        <h1 className="font-display text-2xl text-deep-navy mb-2">Help Us Improve</h1>
        <p className="font-body text-[14px] text-cool-grey mb-6">
          What could we do better?
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 font-body text-[12px]">
            {error}
          </div>
        )}

        <div className="space-y-4 mb-6">
          <div>
            <label className="block font-body text-[12px] font-semibold text-deep-navy mb-2">
              What was missing?
            </label>
            <div className="space-y-2">
              {[
                { id: 'mission', label: 'Organization mission/programs not clear' },
                { id: 'donation', label: 'Hard to find donation link' },
                { id: 'contact', label: 'No contact information' },
                { id: 'volunteer', label: 'Volunteer opportunities unclear' },
                { id: 'other', label: 'Other' }
              ].map(opt => (
                <label key={opt.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="category"
                    value={opt.id}
                    checked={category === opt.id}
                    onChange={e => setCategory(e.target.value)}
                    className="w-4 h-4"
                  />
                  <span className="font-body text-[13px] text-deep-navy">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block font-body text-[12px] font-semibold text-deep-navy mb-2">
              Additional comments (optional)
            </label>
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Let us know what we can improve..."
              rows={3}
              className="w-full px-3 py-2.5 border border-light-grey rounded-lg font-body text-[13px] resize-none focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
          </div>
        </div>

        <button
          onClick={() => submitFeedback('no', category, message)}
          disabled={!category || submitting}
          className="w-full py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {submitting ? 'Sending...' : 'Send Feedback'}
        </button>

        <p className="font-body text-[11px] text-cool-grey text-center mt-4">
          Your feedback is anonymous and never shared with organizations.
        </p>
      </div>
    </div>
  )
}
