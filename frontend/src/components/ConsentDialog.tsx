import { useState } from 'react'

interface ConsentDialogProps {
  nonprofit_name: string
  nonprofit_ein: string
  hours_logged: number
  service_date: string
  notes?: string
  onConsent: () => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

export default function ConsentDialog({
  nonprofit_name,
  nonprofit_ein,
  hours_logged,
  service_date,
  notes,
  onConsent,
  onCancel,
  isLoading = false,
}: ConsentDialogProps) {
  const [error, setError] = useState<string | null>(null)

  const handleConsent = async () => {
    try {
      setError(null)
      await onConsent()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save consent'
      setError(message)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-8 shadow-lg">
        <h2 className="text-2xl font-display text-deep-navy mb-4">Share Hours with Nonprofit?</h2>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-deep-navy mb-3">
            You're about to log volunteer hours with:
          </p>
          <p className="font-semibold text-deep-navy mb-4">{nonprofit_name}</p>

          <div className="space-y-2 text-sm text-cool-grey">
            <div>
              <span className="font-medium text-deep-navy">Date:</span> {service_date}
            </div>
            <div>
              <span className="font-medium text-deep-navy">Hours:</span> {hours_logged}
            </div>
            {notes && (
              <div>
                <span className="font-medium text-deep-navy">Notes:</span> "{notes}"
              </div>
            )}
          </div>
        </div>

        <div className="bg-warm-cream rounded-lg p-4 mb-6">
          <p className="text-sm text-deep-navy mb-3 font-medium">They will see:</p>
          <ul className="text-sm text-cool-grey space-y-1">
            <li>✓ Volunteer date and hours</li>
            <li>✓ Your notes (if provided)</li>
            <li>✗ Your name or email</li>
            <li>✗ Your other volunteer history</li>
          </ul>
        </div>

        <div className="bg-success-green/5 border border-success-green/20 rounded-lg p-4 mb-6">
          <p className="text-sm text-success-green">
            <span className="font-medium">You can:</span>
            <br />
            • Change your mind anytime (revoke access)
            <br />
            • View or delete this record
            <br />
            • Dispute hours if incorrect
          </p>
        </div>

        {error && (
          <div className="bg-destructive/5 border border-destructive/20 rounded-lg p-3 mb-4">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-light-grey rounded-lg font-medium text-cool-grey hover:bg-warm-cream disabled:opacity-50 transition-colors"
          >
            Not Now
          </button>
          <button
            onClick={handleConsent}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-soft-gold text-white rounded-lg font-medium hover:bg-bright-gold disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Saving...' : 'I Agree'}
          </button>
        </div>

        <p className="text-xs text-cool-grey text-center mt-4">
          This choice helps us protect your privacy. The nonprofit can't see your identity or other hours.
        </p>
      </div>
    </div>
  )
}
