import React, { useState, useEffect, useRef } from 'react'
import type { WalletOrg, GivingIntent } from '../types/wallet'
import {
  validateAmount,
  validateHours,
  validateIntentNotes,
  logValidationError,
} from '../utils/walletValidation'

interface IntentModalProps {
  org: WalletOrg
  isOpen: boolean
  onClose: () => void
  onSave: (ein: string, intent: GivingIntent) => void
  initialIntent?: GivingIntent
}

type IntentType = 'giving' | 'volunteer' | 'board'
type Frequency = 'year' | 'month' | 'one-time'

interface FormErrors {
  [key: string]: string
}

/**
 * IntentModal: Modal for adding or editing a giving intent
 * Supports three intent types: giving money, volunteering, board opportunity
 * Features: amount/hours validation, notes with character counter, keyboard navigation
 */
export default function IntentModal({
  org,
  isOpen,
  onClose,
  onSave,
  initialIntent,
}: IntentModalProps) {
  // Form state
  const [selectedType, setSelectedType] = useState<IntentType>(
    initialIntent?.type || 'giving'
  )
  const [amount, setAmount] = useState<string>(
    initialIntent?.type === 'giving' && initialIntent.amount
      ? String(initialIntent.amount)
      : ''
  )
  const [frequency, setFrequency] = useState<Frequency>(
    (initialIntent?.frequency as Frequency) || 'year'
  )
  const [hours, setHours] = useState<string>(
    initialIntent?.type === 'volunteer' && initialIntent.hours
      ? String(initialIntent.hours)
      : ''
  )
  const [notes, setNotes] = useState<string>(initialIntent?.notes || '')
  const [errors, setErrors] = useState<FormErrors>({})

  const modalRef = useRef<HTMLDivElement>(null)
  const firstFocusableRef = useRef<HTMLButtonElement>(null)

  // Reset form when modal closes/opens
  useEffect(() => {
    if (!isOpen) {
      setErrors({})
    }
  }, [isOpen])

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Focus trap
  useEffect(() => {
    if (isOpen && firstFocusableRef.current) {
      firstFocusableRef.current.focus()
    }
  }, [isOpen])

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (selectedType === 'giving') {
      if (!amount) {
        newErrors.amount = 'Amount is required'
      } else {
        try {
          validateAmount(parseFloat(amount))
        } catch (err) {
          newErrors.amount = (err as Error).message
        }
      }
    }

    if (selectedType === 'volunteer') {
      if (!hours) {
        newErrors.hours = 'Hours is required'
      } else {
        try {
          validateHours(parseFloat(hours))
        } catch (err) {
          newErrors.hours = (err as Error).message
        }
      }
    }

    if (notes) {
      try {
        validateIntentNotes(notes)
      } catch (err) {
        newErrors.notes = (err as Error).message
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle save
  const handleSave = () => {
    if (!validateForm()) {
      return
    }

    const intent: GivingIntent = {
      type: selectedType,
      status: 'interested',
      addedAt: initialIntent?.addedAt || Date.now(),
      notes: notes || undefined,
    }

    // Add optional fields based on type
    if (selectedType === 'giving' && amount) {
      intent.amount = Math.floor(parseFloat(amount))
      intent.frequency = frequency
    }

    if (selectedType === 'volunteer' && hours) {
      intent.hours = parseFloat(hours)
    }

    onSave(org.ein, intent)
    onClose()
  }

  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="bg-white rounded-lg shadow-lg max-w-md w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-light-grey">
          <h2 id="modal-title" className="text-lg font-semibold text-deep-navy">
            Add Giving Intent for {org.name}
          </h2>
          <button
            ref={firstFocusableRef}
            onClick={onClose}
            aria-label="Close"
            className="ml-2 p-1 hover:bg-warm-cream rounded transition-colors"
          >
            <svg
              className="w-5 h-5 text-cool-grey hover:text-deep-navy"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Intent Type Selection */}
          <div>
            <fieldset>
              <legend className="text-sm font-semibold text-deep-navy mb-3">
                What would you like to do?
              </legend>
              <div className="space-y-2">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="intent-type"
                    value="giving"
                    checked={selectedType === 'giving'}
                    onChange={() => {
                      setSelectedType('giving')
                      setErrors({})
                    }}
                    className="w-4 h-4 text-soft-gold"
                    aria-label="Give Money"
                  />
                  <span className="ml-3 text-sm text-deep-navy font-medium">Give Money</span>
                </label>

                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="intent-type"
                    value="volunteer"
                    checked={selectedType === 'volunteer'}
                    onChange={() => {
                      setSelectedType('volunteer')
                      setErrors({})
                    }}
                    className="w-4 h-4 text-soft-gold"
                    aria-label="Volunteer"
                  />
                  <span className="ml-3 text-sm text-deep-navy font-medium">Volunteer</span>
                </label>

                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="intent-type"
                    value="board"
                    checked={selectedType === 'board'}
                    onChange={() => {
                      setSelectedType('board')
                      setErrors({})
                    }}
                    className="w-4 h-4 text-soft-gold"
                    aria-label="Join Board"
                  />
                  <span className="ml-3 text-sm text-deep-navy font-medium">Join Board</span>
                </label>
              </div>
            </fieldset>
          </div>

          {/* Giving Money Form */}
          {selectedType === 'giving' && (
            <div className="space-y-4 border-t border-light-grey pt-4">
              <div>
                <label className="block text-sm font-semibold text-deep-navy mb-2">
                  Amount
                </label>
                <div className="flex items-center gap-2">
                  <span className="text-cool-grey">$</span>
                  <input
                    type="number"
                    min="1"
                    max="999999"
                    value={amount}
                    onChange={(e) => {
                      setAmount(e.target.value)
                      if (errors.amount) {
                        const newErrors = { ...errors }
                        delete newErrors.amount
                        setErrors(newErrors)
                      }
                    }}
                    placeholder="0"
                    aria-label="Amount"
                    className={`flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 ${
                      errors.amount
                        ? 'border-red-500 focus:ring-red-500'
                        : 'border-light-grey focus:ring-soft-gold'
                    }`}
                  />
                </div>
                {errors.amount && (
                  <p className="text-red-600 text-xs mt-1">{errors.amount}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-deep-navy mb-2">
                  Frequency
                </label>
                <div className="space-y-2">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="frequency"
                      value="year"
                      checked={frequency === 'year'}
                      onChange={() => setFrequency('year')}
                      className="w-4 h-4 text-soft-gold"
                      aria-label="Per Year"
                    />
                    <span className="ml-3 text-sm text-deep-navy">Per Year</span>
                  </label>

                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="frequency"
                      value="month"
                      checked={frequency === 'month'}
                      onChange={() => setFrequency('month')}
                      className="w-4 h-4 text-soft-gold"
                      aria-label="Per Month"
                    />
                    <span className="ml-3 text-sm text-deep-navy">Per Month</span>
                  </label>

                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="frequency"
                      value="one-time"
                      checked={frequency === 'one-time'}
                      onChange={() => setFrequency('one-time')}
                      className="w-4 h-4 text-soft-gold"
                      aria-label="One-time"
                    />
                    <span className="ml-3 text-sm text-deep-navy">One-time</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Volunteering Form */}
          {selectedType === 'volunteer' && (
            <div className="space-y-4 border-t border-light-grey pt-4">
              <div>
                <label className="block text-sm font-semibold text-deep-navy mb-2">
                  Hours per Week
                </label>
                <input
                  type="number"
                  min="0"
                  max="168"
                  step="0.5"
                  value={hours}
                  onChange={(e) => {
                    setHours(e.target.value)
                    if (errors.hours) {
                      const newErrors = { ...errors }
                      delete newErrors.hours
                      setErrors(newErrors)
                    }
                  }}
                  placeholder="0"
                  aria-label="Hours"
                  className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 ${
                    errors.hours
                      ? 'border-red-500 focus:ring-red-500'
                      : 'border-light-grey focus:ring-soft-gold'
                  }`}
                />
                {errors.hours && (
                  <p className="text-red-600 text-xs mt-1">{errors.hours}</p>
                )}
              </div>
            </div>
          )}

          {/* Notes (for all types) */}
          <div className="border-t border-light-grey pt-4">
            <label className="block text-sm font-semibold text-deep-navy mb-2">
              Notes (optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => {
                setNotes(e.target.value.slice(0, 200))
                if (errors.notes) {
                  const newErrors = { ...errors }
                  delete newErrors.notes
                  setErrors(newErrors)
                }
              }}
              placeholder="Add any notes about your interest..."
              maxLength={200}
              aria-label="Notes"
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 resize-none h-24 ${
                errors.notes
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-light-grey focus:ring-soft-gold'
              }`}
            />
            <div className="flex justify-between items-center mt-1">
              {errors.notes && (
                <p className="text-red-600 text-xs">{errors.notes}</p>
              )}
              <p className="text-xs text-cool-grey ml-auto">
                {notes.length} / 200
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 justify-end p-6 border-t border-light-grey">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-warm-cream text-deep-navy rounded-lg text-sm font-medium hover:bg-warm-cream/70 transition-colors border border-light-grey"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-soft-gold text-white rounded-lg text-sm font-medium hover:bg-soft-gold/90 transition-colors"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
