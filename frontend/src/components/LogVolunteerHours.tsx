import { useState, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { logVolunteerHours } from '../data/api'

interface LogVolunteerHoursProps {
  onSuccess?: () => void
}

export default function LogVolunteerHours({ onSuccess }: LogVolunteerHoursProps) {
  const { getIdToken } = useAuth()
  const [formData, setFormData] = useState({
    nonprofit_name: '',
    nonprofit_ein: '',
    service_date: '',
    hours_logged: '',
    notes: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const validate = useCallback(() => {
    const newErrors: Record<string, string> = {}

    if (!formData.nonprofit_name.trim()) {
      newErrors.nonprofit_name = 'Nonprofit name is required'
    }
    if (!formData.service_date) {
      newErrors.service_date = 'Date is required'
    }
    if (!formData.hours_logged) {
      newErrors.hours_logged = 'Hours is required'
    } else {
      const hours = parseFloat(formData.hours_logged)
      if (isNaN(hours) || hours <= 0 || hours > 24) {
        newErrors.hours_logged = 'Hours must be between 0 and 24'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [formData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    setLoading(true)
    try {
      const idToken = await getIdToken()
      if (!idToken) {
        setErrors({ submit: 'Authentication failed. Please sign in again.' })
        setLoading(false)
        return
      }

      await logVolunteerHours(
        idToken,
        formData.nonprofit_ein.trim(),
        formData.nonprofit_name.trim(),
        formData.service_date,
        parseFloat(formData.hours_logged),
        formData.notes.trim(),
      )

      setSuccess(true)
      setFormData({
        nonprofit_name: '',
        nonprofit_ein: '',
        service_date: '',
        hours_logged: '',
        notes: '',
      })
      setTimeout(() => {
        setSuccess(false)
        onSuccess?.()
      }, 2000)
    } catch (err) {
      setErrors({ submit: err instanceof Error ? err.message : 'An error occurred. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-green-800 font-medium">✓ Volunteer hours logged successfully</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Nonprofit Name */}
        <div>
          <label className="block text-sm font-medium text-deep-navy mb-2">
            Nonprofit Name *
          </label>
          <input
            type="text"
            name="nonprofit_name"
            value={formData.nonprofit_name}
            onChange={handleChange}
            placeholder="e.g., The Beacon of Downtown Houston"
            className={`w-full px-3 py-2 border rounded-lg font-body text-sm ${
              errors.nonprofit_name ? 'border-red-500' : 'border-light-grey'
            } focus:outline-none focus:ring-2 focus:ring-soft-gold/30`}
          />
          {errors.nonprofit_name && <p className="text-xs text-red-600 mt-1">{errors.nonprofit_name}</p>}
        </div>

        {/* EIN (Optional) */}
        <div>
          <label className="block text-sm font-medium text-deep-navy mb-2">
            Nonprofit EIN (Optional)
          </label>
          <input
            type="text"
            name="nonprofit_ein"
            value={formData.nonprofit_ein}
            onChange={handleChange}
            placeholder="e.g., 71-0933434"
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
          />
          <p className="text-xs text-cool-grey mt-1">Helps us match your nonprofit</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Service Date */}
        <div>
          <label className="block text-sm font-medium text-deep-navy mb-2">
            Date of Service *
          </label>
          <input
            type="date"
            name="service_date"
            value={formData.service_date}
            onChange={handleChange}
            className={`w-full px-3 py-2 border rounded-lg font-body text-sm ${
              errors.service_date ? 'border-red-500' : 'border-light-grey'
            } focus:outline-none focus:ring-2 focus:ring-soft-gold/30`}
          />
          {errors.service_date && <p className="text-xs text-red-600 mt-1">{errors.service_date}</p>}
        </div>

        {/* Hours */}
        <div>
          <label className="block text-sm font-medium text-deep-navy mb-2">
            Hours Volunteered *
          </label>
          <input
            type="number"
            name="hours_logged"
            value={formData.hours_logged}
            onChange={handleChange}
            placeholder="e.g., 3.5"
            min="0"
            max="24"
            step="0.5"
            className={`w-full px-3 py-2 border rounded-lg font-body text-sm ${
              errors.hours_logged ? 'border-red-500' : 'border-light-grey'
            } focus:outline-none focus:ring-2 focus:ring-soft-gold/30`}
          />
          {errors.hours_logged && <p className="text-xs text-red-600 mt-1">{errors.hours_logged}</p>}
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-deep-navy mb-2">
          Notes (Optional)
        </label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="e.g., Event setup and registration desk"
          rows={3}
          className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/30"
        />
      </div>

      {errors.submit && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{errors.submit}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-3 bg-soft-gold text-white rounded-lg font-medium hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Logging...' : 'Log Volunteer Hours'}
      </button>

      <p className="text-xs text-cool-grey text-center">
        This is your personal record. A nonprofit can verify these hours later.
      </p>
    </form>
  )
}
