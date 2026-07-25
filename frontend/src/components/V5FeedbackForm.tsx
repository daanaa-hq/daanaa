import { useState } from 'react'
import type { ApiOrganization } from '../data/api'
import { CardPattern } from './ui/CardPattern'

interface V5FeedbackProps {
  org: ApiOrganization
  archetype?: string
}

export default function V5FeedbackForm({ org, archetype }: V5FeedbackProps) {
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [clarity, setClarity] = useState<string>('')
  const [help, setHelp] = useState<string>('')
  const [preference, setPreference] = useState<string>('')
  const [ntee, setNtee] = useState<string>('')
  const [otherFeedback, setOtherFeedback] = useState<string>('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!clarity || !preference) {
      alert('Please answer the clarity and preference questions')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/v5_feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein: org.EIN,
          org_name: org.organization_name,
          archetype,
          clarity: clarity === 'yes',
          clarity_reason: help || null,
          preference: preference === 'peer',
          ntee_funding: ntee || null,
          other_feedback: otherFeedback || null,
          timestamp: new Date().toISOString(),
        }),
      })

      if (response.ok) {
        setSubmitted(true)
        setTimeout(() => setSubmitted(false), 5000)
        setClarity('')
        setHelp('')
        setPreference('')
        setNtee('')
        setOtherFeedback('')
      }
    } catch (err) {
      console.error('Feedback submission failed:', err)
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <CardPattern variant="subtle" className="font-body text-sm text-deep-navy">
        Thanks for your feedback. It helps us improve this comparison.
      </CardPattern>
    )
  }

  const radioClass = "w-4 h-4 accent-[#C9A96E]"
  const inputClass = "w-full px-3 py-2.5 border border-light-grey rounded-lg font-body text-sm text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/50 focus:border-soft-gold"
  const labelClass = "block font-body text-[13px] font-medium text-deep-navy mb-1.5"

  return (
    <CardPattern variant="subtle" className="space-y-4">
      <form onSubmit={handleSubmit} className="contents">
      <p className="font-body text-[13px] font-semibold text-deep-navy">Help us improve this financial comparison</p>

      {/* Clarity */}
      <div className="space-y-2">
        <label className={labelClass}>1. Does this financial comparison make sense to you?</label>
        <div className="flex gap-5">
          {[['yes', 'Yes, it\'s clear'], ['no', 'Not really']].map(([val, lbl]) => (
            <label key={val} className="flex items-center gap-2 font-body text-sm text-deep-navy cursor-pointer">
              <input type="radio" name="clarity" value={val} checked={clarity === val}
                onChange={e => setClarity(e.target.value)} className={radioClass} />
              {lbl}
            </label>
          ))}
        </div>
      </div>

      {/* Help text */}
      {clarity === 'no' && (
        <div className="space-y-1.5">
          <label htmlFor="help" className={labelClass}>What would help you understand better?</label>
          <textarea id="help" value={help} onChange={e => setHelp(e.target.value)}
            className={inputClass} rows={2}
            placeholder="e.g., more explanation of what 'peer group' means" />
        </div>
      )}

      {/* Preference */}
      <div className="space-y-2">
        <label className={labelClass}>2. Is peer comparison more helpful than a single number score?</label>
        <div className="flex flex-wrap gap-5">
          {[['peer', 'Peer comparison is better'], ['single', 'Single score is better'], ['both', 'Both are useful']].map(([val, lbl]) => (
            <label key={val} className="flex items-center gap-2 font-body text-sm text-deep-navy cursor-pointer">
              <input type="radio" name="preference" value={val} checked={preference === val}
                onChange={e => setPreference(e.target.value)} className={radioClass} />
              {lbl}
            </label>
          ))}
        </div>
      </div>

      {/* NTEE (conditional) */}
      {['B', 'C', 'E', 'L', 'N', 'S', 'U'].includes(org.NTEE1 || '') && (
        <div className="space-y-1.5">
          <label htmlFor="ntee" className={labelClass}>3. For this org, what's the primary funding source?</label>
          <select id="ntee" value={ntee} onChange={e => setNtee(e.target.value)} className={inputClass}>
            <option value="">Select one...</option>
            <option value="donations">Donations from individuals</option>
            <option value="grants">Grants from foundations or government</option>
            <option value="fees">Fees for services</option>
            <option value="membership">Membership dues</option>
            <option value="endowment">Endowment or investment income</option>
            <option value="mixed">Mix of the above</option>
            <option value="unsure">Not sure</option>
          </select>
        </div>
      )}

      {/* Other feedback */}
      <div className="space-y-1.5">
        <label htmlFor="other" className={labelClass}>4. Any other feedback?</label>
        <textarea id="other" value={otherFeedback} onChange={e => setOtherFeedback(e.target.value)}
          className={inputClass} rows={2} placeholder="Optional — anything else we should know" />
      </div>

      <button type="submit" disabled={loading}
        className="w-full px-4 py-2.5 bg-soft-gold text-deep-navy font-body text-sm font-semibold rounded-lg hover:bg-bright-gold transition-colors disabled:opacity-50">
        {loading ? 'Sending...' : 'Send feedback'}
      </button>

      <p className="font-body text-[11px] text-cool-grey text-center">
        Anonymous — helps us improve the comparison system.
      </p>
      </form>
    </CardPattern>
  )
}
