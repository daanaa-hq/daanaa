import React, { useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'

interface SubmissionForm {
  ein: string
  volunteer_name: string
  volunteer_email: string
  hours: number
  service_date: string
  activity_description: string
}

export default function VolunteerSubmission() {
  usePageMeta('Log Volunteer Hours | Daanaa', 'Submit your volunteer hours for an organization')

  const [form, setForm] = useState<SubmissionForm>({
    ein: '',
    volunteer_name: '',
    volunteer_email: '',
    hours: 0,
    service_date: new Date().toISOString().split('T')[0],
    activity_description: '',
  })

  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setForm(prev => ({
      ...prev,
      [name]: name === 'hours' ? parseFloat(value) || 0 : value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setSuccess(null)
    setError(null)

    try {
      // Convert EIN to auth token format (nonprofit uses EIN as bearer token)
      const response = await fetch('/api/nonprofit/volunteer-hours', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${form.ein}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          volunteer_name: form.volunteer_name,
          volunteer_email: form.volunteer_email,
          hours: form.hours,
          service_date: form.service_date,
          activity_description: form.activity_description,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to submit hours')
      }

      const data = await response.json()
      setSuccess(true)
      setForm({
        ein: '',
        volunteer_name: '',
        volunteer_email: '',
        hours: 0,
        service_date: new Date().toISOString().split('T')[0],
        activity_description: '',
      })

      // Auto-hide success after 5 seconds
      setTimeout(() => setSuccess(null), 5000)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-soft-cream p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-3xl text-deep-navy mb-2">Log Your Volunteer Hours</h1>
          <p className="text-cool-grey">Record your volunteer contributions for an organization</p>
        </div>

        {success && (
          <div className="bg-soft-gold/10 border border-soft-gold/30 rounded-lg p-4 mb-6 font-body text-sm text-deep-navy">
            Your volunteer hours have been submitted. The organization's director will review and verify them.
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-lg p-8 border border-light-grey space-y-6">
          <div>
            <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
              Organization EIN
            </label>
            <input
              type="text"
              name="ein"
              placeholder="e.g., 12-3456789"
              value={form.ein}
              onChange={handleChange}
              required
              maxLength={10}
              className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50 font-body text-sm"
            />
            <p className="text-xs text-cool-grey mt-1">You can find this on the organization's nonprofit profile</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
                Your Name
              </label>
              <input
                type="text"
                name="volunteer_name"
                placeholder="Full name"
                value={form.volunteer_name}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50 font-body text-sm"
              />
            </div>

            <div>
              <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
                Your Email
              </label>
              <input
                type="email"
                name="volunteer_email"
                placeholder="email@example.com"
                value={form.volunteer_email}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50 font-body text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
                Hours Volunteered
              </label>
              <input
                type="number"
                name="hours"
                placeholder="e.g., 4"
                value={form.hours || ''}
                onChange={handleChange}
                required
                min="0"
                step="0.5"
                max="24"
                className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50 font-body text-sm"
              />
            </div>

            <div>
              <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
                Service Date
              </label>
              <input
                type="date"
                name="service_date"
                value={form.service_date}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50 font-body text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block font-body text-sm font-semibold text-deep-navy mb-2">
              What did you do?
            </label>
            <textarea
              name="activity_description"
              placeholder="Describe the activity you volunteered for (e.g., tutoring students, food delivery, event setup)"
              value={form.activity_description}
              onChange={handleChange}
              required
              maxLength={500}
              rows={4}
              className="w-full px-4 py-2 border border-light-grey rounded-lg focus:outline-none focus:ring-2 focus:ring-soft-gold/50 font-body text-sm resize-none"
            />
            <p className="text-xs text-cool-grey mt-1">{form.activity_description.length}/500 characters</p>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-soft-gold text-deep-navy font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Volunteer Hours'}
            </button>
          </div>

          <p className="text-xs text-cool-grey text-center">
            The organization's director will review and verify your hours before they're recorded.
          </p>
        </form>
      </div>
    </div>
  )
}
