import { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { getApiBase } from '../utils/env'

interface NeedFormState {
  need_type: 'FUNDING' | 'VOLUNTEER' | ''
  title: string
  description: string
  amount_needed?: number
  deadline_date?: string
  cause_area?: string
  service_states: string[]
}

/**
 * NeedIntakeForm: Nonprofit creates/edits a Need
 *
 * Part of Phase 3B (Needs Network backend).
 * Allows nonprofits to submit:
 * - FUNDING: "We need $X to [do Y] by [date]"
 * - VOLUNTEER: "We need volunteers to [do Y]"
 *
 * Stewardship P4 (small org fairness):
 * - Simple form, low friction
 * - Optional fields (smart defaults)
 * - AI draft generation ready (backend feature)
 * - Nonprofit full control over content
 */
export default function NeedIntakeForm({ onSuccess }: { onSuccess?: (needId: string) => void }) {
  const { ein } = useParams<{ ein: string }>()
  const [form, setForm] = useState<NeedFormState>({
    need_type: '',
    title: '',
    description: '',
    cause_area: '',
    service_states: [],
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleChange = useCallback((field: keyof NeedFormState, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }, [])

  const handleStateToggle = useCallback((state: string) => {
    setForm(prev => ({
      ...prev,
      service_states: prev.service_states.includes(state)
        ? prev.service_states.filter(s => s !== state)
        : [...prev.service_states, state]
    }))
  }, [])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    // Validation
    if (!form.need_type || !form.title || !form.description) {
      setError('Need type, title, and description are required')
      setLoading(false)
      return
    }

    if (form.need_type === 'FUNDING' && (!form.amount_needed || form.amount_needed <= 0)) {
      setError('Funding amount must be greater than 0')
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${getApiBase()}/api/nonprofits/${ein}/needs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          need_type: form.need_type,
          title: form.title,
          description: form.description,
          amount_needed: form.need_type === 'FUNDING' ? form.amount_needed : undefined,
          deadline_date: form.deadline_date || undefined,
          cause_area: form.cause_area || undefined,
          service_states: form.service_states.length > 0 ? form.service_states : undefined,
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to create Need')
      }

      const data = await response.json()
      setSuccess(true)
      setForm({
        need_type: '',
        title: '',
        description: '',
        cause_area: '',
        service_states: [],
      })

      if (onSuccess) {
        onSuccess(data.need_id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [form, ein])

  const US_STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

  const CAUSE_AREAS = ['Animal', 'Arts', 'Education', 'Environment', 'Food', 'Health',
    'Housing', 'International', 'Job Training', 'Mental Health', 'Poverty', 'Youth']

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg border border-light-grey">
      <h2 className="text-2xl font-display font-bold text-deep-navy mb-6">Submit a Need</h2>

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
          ✅ Need created successfully! Check your dashboard to review and publish.
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Need Type */}
        <div>
          <label className="block font-medium text-deep-navy mb-3">What do you need help with?</label>
          <div className="space-y-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="need_type"
                value="FUNDING"
                checked={form.need_type === 'FUNDING'}
                onChange={(e) => handleChange('need_type', e.target.value)}
                className="w-4 h-4"
              />
              <span className="font-body">💰 Funding (we need money to accomplish something)</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="need_type"
                value="VOLUNTEER"
                checked={form.need_type === 'VOLUNTEER'}
                onChange={(e) => handleChange('need_type', e.target.value)}
                className="w-4 h-4"
              />
              <span className="font-body">🤝 Volunteers (we need people to help)</span>
            </label>
          </div>
        </div>

        {/* Title */}
        <div>
          <label className="block font-medium text-deep-navy mb-2">What's this Need?</label>
          <input
            type="text"
            placeholder="e.g., Summer Camp Scholarships, Meal Prep Volunteers"
            value={form.title}
            onChange={(e) => handleChange('title', e.target.value)}
            className="w-full px-4 py-2 border border-light-grey rounded-lg font-body"
            required
          />
          <p className="text-xs text-cool-grey mt-1">Keep it clear and specific</p>
        </div>

        {/* Description */}
        <div>
          <label className="block font-medium text-deep-navy mb-2">Tell us more</label>
          <textarea
            placeholder="Describe the need, why it matters, and how donors/volunteers can help"
            value={form.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={5}
            className="w-full px-4 py-2 border border-light-grey rounded-lg font-body resize-none"
            required
          />
          <p className="text-xs text-cool-grey mt-1">Be specific and personal</p>
        </div>

        {/* Funding Amount (if FUNDING) */}
        {form.need_type === 'FUNDING' && (
          <div>
            <label className="block font-medium text-deep-navy mb-2">How much do you need?</label>
            <div className="flex items-center gap-2">
              <span className="text-lg">$</span>
              <input
                type="number"
                placeholder="5000"
                value={form.amount_needed || ''}
                onChange={(e) => handleChange('amount_needed', parseInt(e.target.value) || 0)}
                className="flex-1 px-4 py-2 border border-light-grey rounded-lg font-body"
                min="1"
                required
              />
            </div>
          </div>
        )}

        {/* Deadline Date */}
        <div>
          <label className="block font-medium text-deep-navy mb-2">When do you need this? (optional)</label>
          <input
            type="date"
            value={form.deadline_date || ''}
            onChange={(e) => handleChange('deadline_date', e.target.value)}
            className="w-full px-4 py-2 border border-light-grey rounded-lg font-body"
          />
        </div>

        {/* Cause Area */}
        <div>
          <label className="block font-medium text-deep-navy mb-3">What cause area? (optional)</label>
          <select
            value={form.cause_area || ''}
            onChange={(e) => handleChange('cause_area', e.target.value)}
            className="w-full px-4 py-2 border border-light-grey rounded-lg font-body"
          >
            <option value="">Select a cause...</option>
            {CAUSE_AREAS.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>

        {/* Service States */}
        <div>
          <label className="block font-medium text-deep-navy mb-3">Where do you operate? (optional)</label>
          <div className="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto p-2 border border-light-grey rounded-lg bg-warm-cream/20">
            {US_STATES.map(state => (
              <label key={state} className="flex items-center gap-2 cursor-pointer text-sm">
                <input
                  type="checkbox"
                  checked={form.service_states.includes(state)}
                  onChange={() => handleStateToggle(state)}
                  className="w-4 h-4"
                />
                <span>{state}</span>
              </label>
            ))}
          </div>
          {form.service_states.length === 0 && (
            <p className="text-xs text-cool-grey mt-1">Leave unchecked for NATIONAL scope</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full px-6 py-3 bg-deep-navy text-white font-body font-medium rounded-lg hover:bg-deep-navy/90 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Creating...' : '✨ Create Need'}
        </button>
      </form>

      <div className="mt-6 p-4 bg-soft-gold/10 rounded-lg text-sm text-cool-grey">
        <p className="font-medium mb-2">💡 Tip:</p>
        <p>Your Need will be saved as a draft. Review it, make edits, then publish when ready. We'll ask you to confirm it's still valid every month.</p>
      </div>
    </div>
  )
}
