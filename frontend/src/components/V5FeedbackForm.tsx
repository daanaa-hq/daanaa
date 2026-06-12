import { useState } from 'react'
import type { ApiOrganization } from '../data/api'

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
      <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-700">
        ✓ Thanks for your feedback. It helps us improve this comparison system.
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-4 text-sm">
      <p className="font-semibold text-gray-900">We'd appreciate your feedback on this financial comparison</p>

      {/* Clarity */}
      <div className="space-y-2">
        <label className="font-medium text-gray-700">1. Does this financial comparison make sense to you?</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="clarity"
              value="yes"
              checked={clarity === 'yes'}
              onChange={(e) => setClarity(e.target.value)}
              className="w-4 h-4"
            />
            <span>Yes, it's clear</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="clarity"
              value="no"
              checked={clarity === 'no'}
              onChange={(e) => setClarity(e.target.value)}
              className="w-4 h-4"
            />
            <span>Not really</span>
          </label>
        </div>
      </div>

      {/* Help text */}
      {clarity === 'no' && (
        <div className="space-y-2">
          <label htmlFor="help" className="block text-gray-700">What would help you understand better?</label>
          <textarea
            id="help"
            value={help}
            onChange={(e) => setHelp(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            placeholder="e.g., more explanation of what 'peer group' means"
          />
        </div>
      )}

      {/* Preference */}
      <div className="space-y-2">
        <label className="font-medium text-gray-700">2. Is peer comparison more helpful than a single number score?</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="preference"
              value="peer"
              checked={preference === 'peer'}
              onChange={(e) => setPreference(e.target.value)}
              className="w-4 h-4"
            />
            <span>Peer comparison is better</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="preference"
              value="single"
              checked={preference === 'single'}
              onChange={(e) => setPreference(e.target.value)}
              className="w-4 h-4"
            />
            <span>Single score is better</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="preference"
              value="both"
              checked={preference === 'both'}
              onChange={(e) => setPreference(e.target.value)}
              className="w-4 h-4"
            />
            <span>Both are useful</span>
          </label>
        </div>
      </div>

      {/* NTEE (conditional) */}
      {['B', 'C', 'E', 'L', 'N', 'S', 'U'].includes(org.NTEE1 || '') && (
        <div className="space-y-2">
          <label htmlFor="ntee" className="block font-medium text-gray-700">
            3. For this org, what's the primary funding source?
          </label>
          <select
            id="ntee"
            value={ntee}
            onChange={(e) => setNtee(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select one...</option>
            <option value="donations">Donations from individuals</option>
            <option value="grants">Grants from foundations/government</option>
            <option value="fees">Fees for services</option>
            <option value="membership">Membership dues</option>
            <option value="endowment">Endowment/investment income</option>
            <option value="mixed">Mix of the above</option>
            <option value="unsure">Not sure</option>
          </select>
        </div>
      )}

      {/* Other feedback */}
      <div className="space-y-2">
        <label htmlFor="other" className="block text-gray-700">4. Any other feedback?</label>
        <textarea
          id="other"
          value={otherFeedback}
          onChange={(e) => setOtherFeedback(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={2}
          placeholder="Optional — anything else we should know"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Sending...' : 'Send Feedback'}
      </button>

      <p className="text-xs text-gray-500 text-center">
        Your feedback is anonymous and helps us improve this system.
      </p>
    </form>
  )
}
