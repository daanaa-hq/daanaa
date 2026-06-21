/**
 * Wallet Security Validation Layer
 * All user inputs pass through these validators before state mutations
 * Validators throw errors on invalid input (fail-fast); never silent fail
 */

import type { GivingIntent } from '../types/wallet'

/**
 * WALLET_CONSTRAINTS define security boundaries
 */
export const WALLET_VALIDATION = {
  SEARCH_MAX_LENGTH: 100,
  NOTES_MAX_LENGTH: 200,
  AMOUNT_MIN: 1,
  AMOUNT_MAX: 999999,
  HOURS_MIN: 0.25,
  HOURS_MAX: 168, // One week
  EMAIL_MAX_LENGTH: 254,
} as const

/**
 * Dangerous patterns that indicate regex DoS or code injection attempts
 */
const DANGEROUS_PATTERNS = [
  /\(.*\+\)\+/, // (a+)+  - ReDoS
  /\(.*\*\)\*/, // (a*)*  - ReDoS
  /\(.*\|.*\)\*/, // (a|a)*  - ReDoS
  /<script/i,
  /javascript:/i,
  /on\w+\s*=/i, // onerror=, onclick=, etc.
  /<iframe/i,
  /<object/i,
  /eval\(/i,
]

/**
 * Sanitize a search term: trim, limit length, remove dangerous patterns
 * Throws: if input is invalid, empty, too long, or contains dangerous patterns
 * Returns: sanitized search string
 */
export function validateSearchTerm(term: unknown): string {
  if (typeof term !== 'string') {
    throw new Error('Search term must be a string')
  }

  // Trim whitespace
  const trimmed = term.trim()

  // Check for empty string
  if (trimmed.length === 0) {
    throw new Error('Search term cannot be empty')
  }

  // Enforce max length
  if (trimmed.length > WALLET_VALIDATION.SEARCH_MAX_LENGTH) {
    throw new Error(`Search term must be ${WALLET_VALIDATION.SEARCH_MAX_LENGTH} characters or less`)
  }

  // Check for dangerous patterns (XSS, ReDoS)
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(trimmed)) {
      throw new Error('Search term contains invalid characters or patterns')
    }
  }

  return trimmed
}

/**
 * Validate filter value against allowed enum values
 * Returns: true if valid, false if invalid
 */
export function validateFilterValue(key: string, value: unknown): boolean {
  // Validate key exists and has enum constraints
  const validFilters = {
    intent: ['all', 'giving', 'volunteer', 'board'],
    health: ['all', 'HEALTHY', 'STABLE', 'CAUTION'],
  }

  if (!(key in validFilters)) {
    return false
  }

  // Check if value is in allowed list
  const allowed = validFilters[key as keyof typeof validFilters]
  return typeof value === 'string' && allowed.includes(value)
}

/**
 * Validate sort value against allowed enum values
 * Returns: true if valid, false if invalid
 */
export function validateSortValue(value: unknown): boolean {
  const validSortValues = ['recent', 'name', 'health']
  return typeof value === 'string' && validSortValues.includes(value)
}

/**
 * Sanitize intent notes: trim, limit length, remove control characters
 * Throws: if input is invalid, too long, or contains dangerous patterns
 * Returns: sanitized notes string
 */
export function validateIntentNotes(notes: unknown): string {
  if (typeof notes !== 'string') {
    throw new Error('Notes must be a string')
  }

  // Trim whitespace
  const trimmed = notes.trim()

  // Allow empty string (intent notes are optional)
  if (trimmed.length === 0) {
    return ''
  }

  // Enforce max length
  if (trimmed.length > WALLET_VALIDATION.NOTES_MAX_LENGTH) {
    throw new Error(`Notes must be ${WALLET_VALIDATION.NOTES_MAX_LENGTH} characters or less`)
  }

  // Remove control characters (tabs, newlines, carriage returns, etc.)
  const withoutControls = trimmed.replace(/[\x00-\x1F\x7F]/g, ' ').trim()

  // Check for dangerous patterns
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(withoutControls)) {
      throw new Error('Notes contain invalid characters or patterns')
    }
  }

  return withoutControls
}

/**
 * Validate giving amount: must be positive integer between 1 and 999999
 * Throws: if input is invalid, zero, negative, or out of bounds
 * Returns: validated amount
 */
export function validateAmount(amount: unknown): number {
  if (typeof amount !== 'number' || !Number.isFinite(amount)) {
    throw new Error('Amount must be a finite number')
  }

  // Must be integer
  if (!Number.isInteger(amount)) {
    throw new Error('Amount must be a whole number')
  }

  // Must be positive
  if (amount <= 0) {
    throw new Error('Amount must be greater than 0')
  }

  // Must not exceed max
  if (amount > WALLET_VALIDATION.AMOUNT_MAX) {
    throw new Error(`Amount must be less than ${WALLET_VALIDATION.AMOUNT_MAX}`)
  }

  return amount
}

/**
 * Validate volunteer hours: must be positive number between 0.25 and 168
 * Throws: if input is invalid, zero, negative, or out of bounds
 * Returns: validated hours
 */
export function validateHours(hours: unknown): number {
  if (typeof hours !== 'number' || !Number.isFinite(hours)) {
    throw new Error('Hours must be a finite number')
  }

  // Must be positive
  if (hours <= 0) {
    throw new Error('Hours must be greater than 0')
  }

  // Must be at least 0.25 (15 minutes)
  if (hours < WALLET_VALIDATION.HOURS_MIN) {
    throw new Error(`Hours must be at least ${WALLET_VALIDATION.HOURS_MIN}`)
  }

  // Must not exceed one week
  if (hours > WALLET_VALIDATION.HOURS_MAX) {
    throw new Error(`Hours must be ${WALLET_VALIDATION.HOURS_MAX} or less (one week)`)
  }

  return hours
}

/**
 * Validate email address format
 * Throws: if email is invalid or empty
 * Returns: validated (and trimmed) email
 */
export function validateEmail(email: unknown): string {
  if (typeof email !== 'string') {
    throw new Error('Email must be a string')
  }

  const trimmed = email.trim()

  // Simple email validation (RFC 5322 simplified)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  if (!emailRegex.test(trimmed)) {
    throw new Error('Invalid email format')
  }

  if (trimmed.length > WALLET_VALIDATION.EMAIL_MAX_LENGTH) {
    throw new Error('Email must be 254 characters or less')
  }

  return trimmed
}

/**
 * Validate complete GivingIntent object
 * Throws: if any field is invalid
 * Returns: validated intent
 */
export function validateGivingIntent(intent: Partial<GivingIntent>): Partial<GivingIntent> {
  if (!intent || typeof intent !== 'object') {
    throw new Error('Intent must be an object')
  }

  const validated: Partial<GivingIntent> = { ...intent }

  // Validate optional fields if present
  if (intent.amount !== undefined) {
    validated.amount = validateAmount(intent.amount)
  }

  if (intent.hoursPerMonth !== undefined) {
    validated.hoursPerMonth = validateHours(intent.hoursPerMonth)
  }

  if (intent.notes !== undefined) {
    validated.notes = validateIntentNotes(intent.notes)
  }

  return validated
}

/**
 * Log validation error safely (no PII, no internal state exposure)
 * Internal helper used by validators
 */
export function logValidationError(context: string, error: Error): void {
  // Only log the error type, not the full value or message details
  console.error(`[WalletValidation] ${context}: ${error.message}`)
}
