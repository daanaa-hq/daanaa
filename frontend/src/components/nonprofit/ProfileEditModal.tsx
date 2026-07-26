import { useState } from 'react'

interface ProfileEditModalProps {
  field: string
  currentValue: string
  onSave: (value: string, reason: string) => Promise<void>
  onClose: () => void
}

export default function ProfileEditModal({ field, currentValue, onSave, onClose }: ProfileEditModalProps) {
  const [newValue, setNewValue] = useState(currentValue)
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const fieldConfig: Record<string, { label: string; minChars: number; maxChars: number; help: string }> = {
    mission: {
      label: 'Mission Statement',
      minChars: 50,
      maxChars: 500,
      help: 'Describe what your organization does and why. 50–500 characters.'
    },
    website: {
      label: 'Website URL',
      minChars: 0,
      maxChars: 500,
      help: 'Your main website (must start with http:// or https://)'
    },
    donate_url: {
      label: 'Donation Link',
      minChars: 0,
      maxChars: 500,
      help: 'Where donors can contribute. Link to your site or a payment processor.'
    },
    programs: {
      label: 'Programs & Services',
      minChars: 100,
      maxChars: 2000,
      help: 'What programs do you offer? Who do you serve? 100–2000 characters.'
    },
    service_areas: {
      label: 'Service Areas',
      minChars: 0,
      maxChars: 500,
      help: 'Geographic areas or communities you serve.'
    }
  }

  const config = fieldConfig[field] || { label: field, minChars: 0, maxChars: 500, help: '' }

  const charCount = newValue.length
  const isValid = charCount >= config.minChars && charCount <= config.maxChars && reason.trim().length > 0

  const handleSave = async () => {
    if (!isValid) return

    setSaving(true)
    setError(null)
    try {
      await onSave(newValue, reason)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" role="presentation">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-lg">
        {/* Header */}
        <div className="sticky top-0 bg-warm-cream border-b border-light-grey px-6 py-4 flex items-center justify-between">
          <h2 className="font-display text-xl text-deep-navy">Edit {config.label}</h2>
          <button
            onClick={onClose}
            disabled={saving}
            className="text-cool-grey hover:text-deep-navy text-2xl leading-none disabled:opacity-50 transition hover:bg-light-grey/30 rounded-lg p-1"
            aria-label="Close edit form"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-6">
          {/* Help Text */}
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <p className="font-body text-small text-slate-900 font-semibold mb-1">About this field</p>
            <p className="font-body text-small text-slate-900">{config.help}</p>
          </div>

          {/* Current Value */}
          {currentValue && (
            <div>
              <label className="block font-body text-label font-semibold text-cool-grey uppercase mb-2">
                Current Value
              </label>
              <div className="p-3 bg-light-grey/30 rounded-lg border border-light-grey">
                <p className="font-body text-small text-deep-navy whitespace-pre-wrap">{currentValue}</p>
              </div>
            </div>
          )}

          {/* New Value */}
          <div>
            <label htmlFor="new-value" className="block font-body text-label font-semibold text-cool-grey uppercase mb-2">
              New Value
            </label>
            {field === 'website' || field === 'donate_url' ? (
              <input
                id="new-value"
                type="url"
                value={newValue}
                onChange={e => setNewValue(e.target.value)}
                placeholder="https://example.com"
                aria-label={`New ${config.label}`}
                className="w-full px-4 py-3 border border-light-grey rounded-lg font-body text-body focus:outline-none focus:ring-2 focus:ring-soft-gold"
              />
            ) : (
              <textarea
                id="new-value"
                value={newValue}
                onChange={e => setNewValue(e.target.value)}
                placeholder={`Enter ${config.label.toLowerCase()}...`}
                rows={6}
                aria-label={`New ${config.label}`}
                className="w-full px-4 py-3 border border-light-grey rounded-lg font-body text-body resize-none focus:outline-none focus:ring-2 focus:ring-soft-gold"
              />
            )}
            <div className="flex items-center justify-between mt-2">
              <span className="font-body text-label text-cool-grey">
                {charCount} / {config.maxChars} characters
              </span>
              {charCount < config.minChars && (
                <span className="font-body text-label text-destructive">
                  Minimum {config.minChars} characters required
                </span>
              )}
            </div>
          </div>

          {/* Reason */}
          <div className="bg-soft-gold/10 p-4 rounded-lg border border-soft-gold/30">
            <label htmlFor="reason" className="block font-body text-label font-semibold text-cool-grey uppercase mb-2">
              ✍️ Why are you making this change?
            </label>
            <textarea
              id="reason"
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="e.g., 'Updated our programs to reflect new initiatives' or 'Corrected outdated information'"
              rows={3}
              aria-label="Reason for profile edit"
              aria-describedby="reason-help"
              className="w-full px-4 py-3 border border-light-grey rounded-lg font-body text-body resize-none focus:outline-none focus:ring-2 focus:ring-soft-gold"
            />
            <p id="reason-help" className="font-body text-label text-cool-grey mt-2">
              This message helps donors understand what changed and why. Be concise and honest.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
              <p className="font-body text-small text-destructive">{error}</p>
            </div>
          )}

          {/* Preview */}
          <div className="p-4 bg-success-green/5 rounded-lg border border-success-green/20">
            <p className="font-body text-caption font-semibold text-success-green mb-2">Preview</p>
            <p className="font-body text-small text-success-green whitespace-pre-wrap">{newValue || '(empty)'}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-warm-cream border-t border-light-grey px-6 py-4 flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2.5 rounded-lg border border-light-grey text-deep-navy font-body text-body font-semibold hover:bg-light-grey/30 disabled:opacity-50 transition"
            aria-label="Cancel edits"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!isValid || saving}
            className="px-6 py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold disabled:opacity-50 disabled:cursor-not-allowed transition"
            aria-label={`Save changes to ${config.label}`}
            aria-disabled={!isValid || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
