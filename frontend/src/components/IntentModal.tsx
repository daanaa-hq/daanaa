import React, { useState, useEffect, useRef } from 'react'
import type { WalletOrg, GivingIntent } from '../types/wallet'
import {
  validateAmount,
  validateHours,
  validateIntentNotes,
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
type Step = 'type' | 'details'

interface FormErrors {
  [key: string]: string
}

export default function IntentModal({
  org,
  isOpen,
  onClose,
  onSave,
  initialIntent,
}: IntentModalProps) {
  const isEditing = !!initialIntent

  const [step, setStep] = useState<Step>(isEditing ? 'details' : 'type')
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

  useEffect(() => {
    if (!isOpen) {
      if (!isEditing) {
        setStep('type')
        setSelectedType('giving')
        setAmount('')
        setFrequency('year')
        setHours('')
        setNotes('')
      }
      setErrors({})
    }
  }, [isOpen, isEditing])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  useEffect(() => {
    if (isOpen && firstFocusableRef.current) {
      firstFocusableRef.current.focus()
    }
  }, [isOpen, step])

  const handleTypeSelect = (type: IntentType) => {
    setSelectedType(type)
    setErrors({})
    setStep('details')
  }

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (selectedType === 'giving' && amount) {
      try {
        validateAmount(parseFloat(amount))
      } catch (err) {
        newErrors.amount = (err as Error).message
      }
    }

    if (selectedType === 'volunteer' && hours) {
      try {
        validateHours(parseFloat(hours))
      } catch (err) {
        newErrors.hours = (err as Error).message
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

  const handleSave = () => {
    if (!validateForm()) return

    const intent: GivingIntent = {
      type: selectedType,
      status: 'interested',
      addedAt: initialIntent?.addedAt || Date.now(),
      notes: notes || undefined,
    }

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

  if (!isOpen) return null

  const typeLabels: Record<IntentType, { label: string; sub: string; icon: React.ReactNode }> = {
    giving: {
      label: 'Give money',
      sub: 'Donate to their work',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
      ),
    },
    volunteer: {
      label: 'Volunteer',
      sub: 'Give your time',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      ),
    },
    board: {
      label: 'Join the board',
      sub: 'Govern and guide',
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <path d="M3 9h18M9 21V9"/>
        </svg>
      ),
    },
  }

  const selectedTypeLabel = typeLabels[selectedType]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="bg-white rounded-t-2xl sm:rounded-2xl shadow-xl w-full sm:max-w-md max-h-[92dvh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4">
          <div>
            {step === 'details' && !isEditing && (
              <button
                onClick={() => setStep('type')}
                className="mb-2 inline-flex items-center gap-1 font-body text-[12px] text-cool-grey hover:text-deep-navy transition-colors"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
                Back
              </button>
            )}
            <h2 id="modal-title" className="font-display italic text-[20px] text-deep-navy leading-snug">
              {step === 'type'
                ? `How would you like to support ${org.name}?`
                : isEditing
                  ? `Edit your intent for ${org.name}`
                  : `${selectedTypeLabel.label} for ${org.name}`}
            </h2>
          </div>
          <button
            ref={firstFocusableRef}
            onClick={onClose}
            aria-label="Close"
            className="ml-3 mt-0.5 p-1.5 rounded-lg text-cool-grey hover:text-deep-navy hover:bg-light-grey/40 transition-colors shrink-0"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Step 1: Type selection */}
        {step === 'type' && (
          <div className="px-6 pb-6 space-y-3">
            {(['giving', 'volunteer', 'board'] as IntentType[]).map((type) => {
              const t = typeLabels[type]
              return (
                <button
                  key={type}
                  onClick={() => handleTypeSelect(type)}
                  className="w-full flex items-center gap-4 px-5 py-4 rounded-2xl border-2 border-light-grey text-left hover:border-soft-gold hover:bg-soft-gold/5 transition-all group"
                >
                  <span className="text-soft-gold group-hover:scale-110 transition-transform shrink-0">
                    {t.icon}
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className="block font-body text-[15px] font-semibold text-deep-navy">{t.label}</span>
                    <span className="block font-body text-[12px] text-cool-grey mt-0.5">{t.sub}</span>
                  </span>
                  <svg className="w-4 h-4 text-cool-grey group-hover:text-soft-gold transition-colors shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              )
            })}

            <button
              onClick={onClose}
              className="w-full py-3 font-body text-[13px] text-cool-grey hover:text-deep-navy transition-colors text-center"
            >
              Not sure yet
            </button>
          </div>
        )}

        {/* Step 2: Details */}
        {step === 'details' && (
          <div className="px-6 pb-6 space-y-5">
            {/* Giving details */}
            {selectedType === 'giving' && (
              <div className="space-y-4">
                <div>
                  <label className="block font-body text-[13px] font-semibold text-deep-navy mb-2">
                    How much? <span className="font-normal text-cool-grey">(optional)</span>
                  </label>
                  <div className="flex items-center gap-2">
                    <span className="font-body text-[15px] text-cool-grey">$</span>
                    <input
                      type="number"
                      min="1"
                      max="999999"
                      value={amount}
                      onChange={(e) => {
                        setAmount(e.target.value)
                        if (errors.amount) {
                          const { amount: _, ...rest } = errors
                          setErrors(rest)
                        }
                      }}
                      placeholder="Leave blank if unsure"
                      aria-label="Amount"
                      className={`flex-1 px-4 py-2.5 border rounded-xl font-body text-[14px] focus:outline-none focus:ring-2 ${
                        errors.amount
                          ? 'border-red-400 focus:ring-red-400'
                          : 'border-light-grey focus:ring-soft-gold/50'
                      }`}
                    />
                  </div>
                  {errors.amount && (
                    <p className="font-body text-red-600 text-[12px] mt-1">{errors.amount}</p>
                  )}
                </div>

                <div>
                  <label className="block font-body text-[13px] font-semibold text-deep-navy mb-2">How often?</label>
                  <div className="flex gap-2">
                    {(['year', 'month', 'one-time'] as Frequency[]).map((f) => (
                      <button
                        key={f}
                        type="button"
                        onClick={() => setFrequency(f)}
                        className={`flex-1 py-2.5 rounded-xl border font-body text-[13px] font-medium transition-all ${
                          frequency === f
                            ? 'border-soft-gold bg-soft-gold/10 text-deep-navy'
                            : 'border-light-grey text-cool-grey hover:border-soft-gold/40'
                        }`}
                      >
                        {f === 'year' ? 'Yearly' : f === 'month' ? 'Monthly' : 'One-time'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Volunteer details */}
            {selectedType === 'volunteer' && (
              <div>
                <label className="block font-body text-[13px] font-semibold text-deep-navy mb-2">
                  Hours per week <span className="font-normal text-cool-grey">(optional)</span>
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
                      const { hours: _, ...rest } = errors
                      setErrors(rest)
                    }
                  }}
                  placeholder="Leave blank if unsure"
                  aria-label="Hours per week"
                  className={`w-full px-4 py-2.5 border rounded-xl font-body text-[14px] focus:outline-none focus:ring-2 ${
                    errors.hours
                      ? 'border-red-400 focus:ring-red-400'
                      : 'border-light-grey focus:ring-soft-gold/50'
                  }`}
                />
                {errors.hours && (
                  <p className="font-body text-red-600 text-[12px] mt-1">{errors.hours}</p>
                )}
              </div>
            )}

            {/* Board: no extra fields, just notes */}
            {selectedType === 'board' && (
              <p className="font-body text-[14px] text-cool-grey leading-[1.6]">
                We will keep track of your interest here. Use the notes below to add any context.
              </p>
            )}

            {/* Notes */}
            <div>
              <label className="block font-body text-[13px] font-semibold text-deep-navy mb-2">
                Notes <span className="font-normal text-cool-grey">(optional)</span>
              </label>
              <textarea
                value={notes}
                onChange={(e) => {
                  setNotes(e.target.value.slice(0, 200))
                  if (errors.notes) {
                    const { notes: _, ...rest } = errors
                    setErrors(rest)
                  }
                }}
                placeholder="Anything you want to remember about this..."
                maxLength={200}
                aria-label="Notes"
                rows={3}
                className={`w-full px-4 py-2.5 border rounded-xl font-body text-[14px] focus:outline-none focus:ring-2 resize-none ${
                  errors.notes
                    ? 'border-red-400 focus:ring-red-400'
                    : 'border-light-grey focus:ring-soft-gold/50'
                }`}
              />
              <div className="flex justify-between items-center mt-1">
                {errors.notes && (
                  <p className="font-body text-red-600 text-[12px]">{errors.notes}</p>
                )}
                <p className="font-body text-[11px] text-cool-grey ml-auto">{notes.length}/200</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl border border-light-grey text-cool-grey font-body text-[13px] font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex-1 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold hover:bg-bright-gold transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
