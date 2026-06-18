import { useState, useCallback, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { logVolunteerHours, getOrganizations } from '../data/api'
import type { ApiOrganization } from '../data/api'

interface LogVolunteerHoursProps {
  onSuccess?: () => void
}

export default function LogVolunteerHours({ onSuccess }: LogVolunteerHoursProps) {
  const { user, getIdToken, signInWithGoogle } = useAuth()
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
  const [allowVerification, setAllowVerification] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ApiOrganization[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [searching, setSearching] = useState(false)
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const handleNonprofitSearch = useCallback(async (query: string) => {
    setSearchQuery(query)
    if (query.trim().length < 2) {
      setSearchResults([])
      setShowDropdown(false)
      return
    }

    setSearching(true)
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await getOrganizations({
          q: query,
          page: 1,
          per_page: 10,
        })
        setSearchResults(results.organizations || [])
        setShowDropdown(true)
      } catch (err) {
        console.error('Error searching organizations:', err)
        setSearchResults([])
      } finally {
        setSearching(false)
      }
    }, 300)
  }, [])

  const handleSelectOrganization = (org: ApiOrganization) => {
    setFormData((prev) => ({
      ...prev,
      nonprofit_name: org.organization_name || '',
      nonprofit_ein: org.EIN || '',
    }))
    setSearchQuery(org.organization_name || '')
    setShowDropdown(false)
    setSearchResults([])
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    if (name === 'nonprofit_name') {
      handleNonprofitSearch(value)
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }))
    }
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [])

  const validate = useCallback(() => {
    const newErrors: Record<string, string> = {}

    const nameToCheck = formData.nonprofit_name || searchQuery
    if (!nameToCheck.trim()) {
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
  }, [formData, searchQuery])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) return

    // Require login before saving
    if (!user) {
      setErrors({ submit: 'Please sign in with Google to save your volunteer hours' })
      return
    }

    setLoading(true)
    try {
      const idToken = await getIdToken()
      if (!idToken) {
        setErrors({ submit: 'Authentication failed. Please try signing in again.' })
        setLoading(false)
        return
      }

      const nameToSubmit = formData.nonprofit_name || searchQuery
      await logVolunteerHours(
        idToken,
        formData.nonprofit_ein.trim(),
        nameToSubmit.trim(),
        formData.service_date,
        parseFloat(formData.hours_logged),
        formData.notes.trim(),
        allowVerification,
      )

      setSuccess(true)
      setFormData({
        nonprofit_name: '',
        nonprofit_ein: '',
        service_date: '',
        hours_logged: '',
        notes: '',
      })
      setSearchQuery('')
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
        {/* Nonprofit Name with Search */}
        <div className="relative">
          <label className="block text-sm font-medium text-deep-navy mb-2">
            Nonprofit Name *
          </label>
          <input
            type="text"
            name="nonprofit_name"
            value={searchQuery || formData.nonprofit_name}
            onChange={handleChange}
            onFocus={() => {
              if (searchQuery && searchResults.length > 0) {
                setShowDropdown(true)
              }
            }}
            placeholder="Search for a nonprofit..."
            autoComplete="off"
            className={`w-full px-3 py-2 border rounded-lg font-body text-sm ${
              errors.nonprofit_name ? 'border-red-500' : 'border-light-grey'
            } focus:outline-none focus:ring-2 focus:ring-soft-gold/30`}
          />
          {searching && (
            <p className="text-xs text-cool-grey mt-1">Searching...</p>
          )}
          {errors.nonprofit_name && <p className="text-xs text-red-600 mt-1">{errors.nonprofit_name}</p>}

          {/* Dropdown Results */}
          {showDropdown && searchResults.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-light-grey rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {searchResults.map((org) => (
                <button
                  key={org.EIN}
                  type="button"
                  onClick={() => handleSelectOrganization(org)}
                  className="w-full text-left px-3 py-2 hover:bg-warm-cream transition-colors border-b border-light-grey/30 last:border-b-0"
                >
                  <p className="font-medium text-deep-navy text-sm">{org.organization_name}</p>
                  <p className="text-xs text-cool-grey">
                    {org.CITY && org.STATE ? `${org.CITY}, ${org.STATE}` : ''} {org.EIN && `(${org.EIN})`}
                  </p>
                </button>
              ))}
            </div>
          )}
          {showDropdown && searchResults.length === 0 && searchQuery && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-light-grey rounded-lg shadow-lg p-3">
              <p className="text-xs text-cool-grey text-center">No organizations found. Enter the name manually.</p>
            </div>
          )}
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

      {/* Consent Checkbox */}
      <div className="flex items-start space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <input
          type="checkbox"
          id="allow_verification"
          checked={allowVerification}
          onChange={(e) => setAllowVerification(e.target.checked)}
          className="mt-1 w-4 h-4 cursor-pointer"
        />
        <label htmlFor="allow_verification" className="text-sm text-deep-navy cursor-pointer">
          <span className="font-medium">Allow {formData.nonprofit_name || 'this nonprofit'} to verify these hours</span>
          <p className="text-xs text-cool-grey mt-1">
            When unchecked, these hours stay private in your wallet. You can change this anytime.
          </p>
        </label>
      </div>

      {errors.submit && (
        <div className={`p-3 rounded-lg ${
          errors.submit.includes('sign in')
            ? 'bg-blue-50 border border-blue-200'
            : 'bg-red-50 border border-red-200'
        }`}>
          <p className={errors.submit.includes('sign in') ? 'text-blue-800 text-sm' : 'text-red-800 text-sm'}>
            {errors.submit}
          </p>
          {errors.submit.includes('sign in') && (
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
