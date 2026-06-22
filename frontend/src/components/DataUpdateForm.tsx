import { useState } from 'react'
import { AlertCircle } from 'lucide-react'
import type { ApiOrganization } from '../data/api'

interface DataUpdateFormProps {
  org: ApiOrganization
  claimToken: string
  ein: string
  onSuccess?: () => void
  onCancel?: () => void
}

interface FormState {
  total_revenue: string
  total_expenses: string
  program_expense_pct: string
  months_of_reserve: string
  explanation: string
  isSubmitting: boolean
  error: string | null
  success: boolean
}

export default function DataUpdateForm({
  org,
  claimToken,
  ein,
  onSuccess,
  onCancel,
}: DataUpdateFormProps) {
  const [form, setForm] = useState<FormState>({
    total_revenue: org.total_revenue ? org.total_revenue.toString() : '',
    total_expenses: org.total_expenses ? org.total_expenses.toString() : '',
    program_expense_pct: org.program_expense_pct ? org.program_expense_pct.toString() : '',
    months_of_reserve: org.months_of_reserve ? org.months_of_reserve.toString() : '',
    explanation: '',
    isSubmitting: false,
    error: null,
    success: false,
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value, error: null }))
  }

  const handleSubmit = async () => {
    setForm(prev => ({ ...prev, isSubmitting: true, error: null }))

    try {
      const updates: Record<string, number> = {}
      const errors: string[] = []

      // Validate and collect updates
      if (form.total_revenue) {
        const val = parseFloat(form.total_revenue)
        if (isNaN(val) || val < 0) {
          errors.push('Revenue must be a positive number')
        } else {
          updates.total_revenue = val
        }
      }

      if (form.total_expenses) {
        const val = parseFloat(form.total_expenses)
        if (isNaN(val) || val < 0) {
          errors.push('Expenses must be a positive number')
        } else {
          updates.total_expenses = val
        }
      }

      if (form.program_expense_pct) {
        const val = parseFloat(form.program_expense_pct)
        if (isNaN(val) || val < 0 || val > 100) {
          errors.push('Program % must be between 0 and 100')
        } else {
          updates.program_expense_pct = val
        }
      }

      if (form.months_of_reserve) {
        const val = parseFloat(form.months_of_reserve)
        if (isNaN(val) || val < 0) {
          errors.push('Months of reserve must be a positive number')
        } else {
          updates.months_of_reserve = val
        }
      }

      if (errors.length > 0) {
        setForm(prev => ({
          ...prev,
          error: errors.join('; '),
          isSubmitting: false,
        }))
        return
      }

      if (Object.keys(updates).length === 0) {
        setForm(prev => ({
          ...prev,
          error: 'Please enter at least one updated value',
          isSubmitting: false,
        }))
        return
      }

      // Submit to API
      const response = await fetch('/api/nonprofit/update-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          claim_token: claimToken,
          ein,
          updates,
          explanation: form.explanation.trim(),
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || data.errors?.join(', ') || 'Failed to submit update')
      }

      setForm(prev => ({
        ...prev,
        success: true,
        isSubmitting: false,
      }))

      if (onSuccess) {
        setTimeout(() => onSuccess(), 2000)
      }
    } catch (error) {
      setForm(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to submit update',
        isSubmitting: false,
      }))
    }
  }

  if (form.success) {
    return (
      <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
        <p className="font-body text-[14px] text-green-800 flex items-center gap-2">
          <span className="text-lg">✅</span>
          Your update was received! It will be included in our next scoring run (within 2-3 business days).
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {form.error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="font-body text-[14px] text-red-700">{form.error}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Annual Revenue</span>
          <div className="relative">
            <span className="absolute left-3 top-2 text-cool-grey">$</span>
            <input
              type="number"
              name="total_revenue"
              value={form.total_revenue}
              onChange={handleChange}
              disabled={form.isSubmitting}
              placeholder="e.g., 3100000"
              className="pl-6 pr-3 py-2 w-full border border-light-cream rounded-lg font-body text-[13px] focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
          </div>
          {org.total_revenue && (
            <p className="text-[10px] text-cool-grey mt-1">
              IRS FY{org.latest_tax_year}: ${(org.total_revenue / 1_000_000).toFixed(2)}M
            </p>
          )}
        </label>

        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Annual Expenses</span>
          <div className="relative">
            <span className="absolute left-3 top-2 text-cool-grey">$</span>
            <input
              type="number"
              name="total_expenses"
              value={form.total_expenses}
              onChange={handleChange}
              disabled={form.isSubmitting}
              placeholder="e.g., 2850000"
              className="pl-6 pr-3 py-2 w-full border border-light-cream rounded-lg font-body text-[13px] focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
          </div>
          {org.total_expenses && (
            <p className="text-[10px] text-cool-grey mt-1">
              IRS FY{org.latest_tax_year}: ${(org.total_expenses / 1_000_000).toFixed(2)}M
            </p>
          )}
        </label>

        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Program Expense %</span>
          <div className="relative">
            <input
              type="number"
              name="program_expense_pct"
              value={form.program_expense_pct}
              onChange={handleChange}
              disabled={form.isSubmitting}
              placeholder="e.g., 81"
              min="0"
              max="100"
              className="pr-6 px-3 py-2 w-full border border-light-cream rounded-lg font-body text-[13px] focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
            <span className="absolute right-3 top-2 text-cool-grey">%</span>
          </div>
          {org.program_expense_pct && (
            <p className="text-[10px] text-cool-grey mt-1">
              IRS FY{org.latest_tax_year}: {org.program_expense_pct.toFixed(1)}%
            </p>
          )}
        </label>

        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Months of Reserve</span>
          <div className="relative">
            <input
              type="number"
              name="months_of_reserve"
              value={form.months_of_reserve}
              onChange={handleChange}
              disabled={form.isSubmitting}
              placeholder="e.g., 3.2"
              step="0.1"
              className="pr-12 px-3 py-2 w-full border border-light-cream rounded-lg font-body text-[13px] focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
            <span className="absolute right-3 top-2 text-cool-grey text-[12px]">mo</span>
          </div>
          {org.months_of_reserve && (
            <p className="text-[10px] text-cool-grey mt-1">
              IRS FY{org.latest_tax_year}: {org.months_of_reserve.toFixed(1)} months
            </p>
          )}
        </label>
      </div>

      <label className="block">
        <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">What changed? <span className="text-muted-cream font-normal">(optional)</span></span>
        <textarea
          name="explanation"
          value={form.explanation}
          onChange={handleChange}
          disabled={form.isSubmitting}
          placeholder="e.g., 2024 was a stronger year with increased fundraising"
          rows={2}
          className="w-full px-3 py-2 border border-light-cream rounded-lg font-body text-[13px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
        />
      </label>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={form.isSubmitting}
          className="px-4 py-2 bg-soft-gold text-deep-navy font-body text-[13px] font-semibold rounded-lg hover:bg-bright-gold disabled:opacity-40 transition-colors"
        >
          {form.isSubmitting ? 'Submitting…' : 'Submit Update'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={form.isSubmitting}
            className="px-4 py-2 bg-light-cream text-cool-grey font-body text-[13px] font-semibold rounded-lg hover:bg-muted-cream disabled:opacity-40 transition-colors"
          >
            Skip for now
          </button>
        )}
      </div>

      <p className="font-body text-[11px] text-cool-grey italic">
        💡 Updates are included in our next scoring run (2-3 business days), giving you time to prepare your story for donors.
      </p>
    </div>
  )
}
