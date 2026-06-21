import React, { useState } from 'react'
import type { DonorTemplate } from '../lib/schemas'

interface TemplateEditorModalProps {
  isOpen: boolean
  onClose: () => void
  nonprofitEin: string
  nonprofitName: string
  authToken: string
  onSave: (template: DonorTemplate) => void
}

const TEMPLATE_VARS = ['{donor_name}', '{amount}', '{date}', '{org_name}']

/**
 * TemplateEditorModal
 *
 * Two-column modal for editing custom donor templates:
 * - Left: Input fields (name, body) + validation hints
 * - Right: Live preview with substituted variables
 *
 * Props:
 *   - isOpen: Whether modal is visible
 *   - onClose: Callback when close/cancel
 *   - nonprofitEin: EIN for API auth
 *   - nonprofitName: Organization name for preview
 *   - authToken: Bearer token
 *   - onSave: Callback on successful save
 */
export default function TemplateEditorModal({
  isOpen,
  onClose,
  nonprofitEin,
  nonprofitName,
  authToken,
  onSave,
}: TemplateEditorModalProps) {
  const [name, setName] = useState('')
  const [body, setBody] = useState('')
  const [validating, setValidating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleClose = () => {
    setName('')
    setBody('')
    setError(null)
    onClose()
  }

  const getPreview = (): string => {
    let result = body
    result = result.replace(/{donor_name}/g, 'Jane Donor')
    result = result.replace(/{amount}/g, '$250.00')
    result = result.replace(/{date}/g, new Date().toISOString().split('T')[0])
    result = result.replace(/{org_name}/g, nonprofitName)
    return result
  }

  const validateInput = (): { valid: boolean; message?: string } => {
    if (!name.trim()) {
      return { valid: false, message: 'Template name is required' }
    }
    if (!body.trim()) {
      return { valid: false, message: 'Template body is required' }
    }
    if (!TEMPLATE_VARS.some(v => body.includes(v))) {
      return {
        valid: false,
        message: `Template must include at least one variable: ${TEMPLATE_VARS.join(', ')}`,
      }
    }
    return { valid: true }
  }

  const handleSave = async () => {
    const validation = validateInput()
    if (!validation.valid) {
      setError(validation.message || 'Invalid input')
      return
    }

    setValidating(true)
    try {
      const response = await fetch('/api/nonprofit/donor-templates', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template_name: name,
          template_body: body,
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.error || 'Failed to save template')
      }

      const saved = await response.json()
      onSave(saved)
      handleClose()

      // Show toast (simple alert for now)
      alert('Template saved successfully!')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setValidating(false)
    }
  }

  const preview = getPreview()
  const hasVars = TEMPLATE_VARS.some(v => body.includes(v))

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-xl">
        {/* Header */}
        <div className="border-b border-light-grey p-6">
          <h2 className="font-display text-2xl text-deep-navy">Create Custom Template</h2>
          <p className="text-sm text-cool-grey mt-1">Add variables to personalize your donor messages</p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Editor */}
            <div className="flex flex-col gap-4">
              {/* Name Input */}
              <div>
                <label className="block text-sm font-semibold text-deep-navy mb-2">
                  Template Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g., Corporate Giving Thank You"
                  className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
                />
              </div>

              {/* Body Textarea */}
              <div className="flex-1 flex flex-col">
                <label className="block text-sm font-semibold text-deep-navy mb-2">
                  Message Template
                </label>
                <textarea
                  value={body}
                  onChange={e => setBody(e.target.value)}
                  placeholder={`Dear {donor_name},\n\nThank you for your {amount} gift on {date}. Your support helps {org_name} make a difference.\n\nWith gratitude,\n{org_name}`}
                  className="flex-1 px-3 py-2 border border-light-grey rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50 resize-none"
                />
              </div>

              {/* Variable Hints */}
              <div className="text-xs text-cool-grey bg-soft-cream p-3 rounded">
                <p className="font-semibold mb-2">Available variables:</p>
                <div className="flex flex-wrap gap-2">
                  {TEMPLATE_VARS.map(v => (
                    <code
                      key={v}
                      className={`px-2 py-1 rounded ${
                        body.includes(v) ? 'bg-green-100 text-green-700' : 'bg-light-grey text-cool-grey'
                      }`}
                    >
                      {v}
                    </code>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Preview */}
            <div className="flex flex-col gap-2">
              <label className="block text-sm font-semibold text-deep-navy">Preview</label>
              <div className="flex-1 bg-soft-cream rounded-lg p-4 border border-light-grey text-sm leading-relaxed overflow-y-auto">
                {body ? (
                  <p className="text-deep-navy whitespace-pre-wrap">{preview}</p>
                ) : (
                  <p className="text-cool-grey italic">Your preview will appear here</p>
                )}
              </div>

              {/* Validation Status */}
              <div className="text-xs">
                {!name && <p className="text-cool-grey">✓ Name required</p>}
                {name && <p className="text-green-600">✓ Name entered</p>}

                {!body && <p className="text-cool-grey">✓ Message required</p>}
                {body && !hasVars && (
                  <p className="text-red-600">✗ Message must include at least one variable</p>
                )}
                {body && hasVars && (
                  <p className="text-green-600">✓ Message includes variables</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-light-grey p-6 flex gap-3 justify-end">
          <button
            onClick={handleClose}
            disabled={validating}
            className="px-4 py-2 text-deep-navy font-semibold rounded-lg hover:bg-light-grey transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={validating || !name || !body || !hasVars}
            className="px-4 py-2 bg-soft-gold text-deep-navy font-semibold rounded-lg hover:bg-bright-gold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {validating ? 'Saving...' : 'Save Template'}
          </button>
        </div>
      </div>
    </div>
  )
}
