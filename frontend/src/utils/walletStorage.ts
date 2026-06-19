/**
 * localStorage persistence layer for wallet data
 * Handles read/write, quota management, and corruption recovery
 * No external dependencies — pure localStorage + JSON + validation
 */

import { type Wallet, isValidWallet } from '../types/wallet'

const STORAGE_KEY = 'daanaa_wallet'
const BACKUP_KEY = 'daanaa_wallet_backup'
const QUOTA_WARNING_THRESHOLD = 90 // percent

interface QuotaInfo {
  used: number // bytes used by wallet key
  available: number // bytes available (estimated)
  percentUsed: number // 0-100
}

interface CorruptionCheck {
  corrupted: boolean
  recovered?: Wallet
  error?: string
}

/**
 * Read wallet from localStorage
 * Returns null if missing or invalid
 */
function read(): Wallet | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) {
      return null
    }

    const parsed = JSON.parse(stored) as unknown
    if (isValidWallet(parsed)) {
      return parsed
    }

    return null
  } catch (err) {
    return null
  }
}

/**
 * Write wallet to localStorage
 * Logs warnings if quota exceeds 90%
 * Catches QuotaExceededError gracefully
 */
function write(wallet: Wallet): void {
  try {
    const serialized = JSON.stringify(wallet)
    localStorage.setItem(STORAGE_KEY, serialized)

    // Check quota and warn if needed
    const quota = getQuotaInfo()
    if (quota.percentUsed > QUOTA_WARNING_THRESHOLD) {
      console.warn(
        `[Wallet] localStorage quota is ${quota.percentUsed.toFixed(1)}% full. ` +
          `Consider exporting or clearing some orgs.`
      )
    }
  } catch (err: any) {
    if (err.name === 'QuotaExceededError') {
      console.error(
        '[Wallet] localStorage quota exceeded. Wallet is full. Please remove some orgs or export.',
        err
      )
    } else {
      console.error('[Wallet] Failed to write wallet to localStorage:', err)
    }
  }
}

/**
 * Clear wallet from localStorage
 */
function clear(): void {
  localStorage.removeItem(STORAGE_KEY)
}

/**
 * Estimate localStorage quota usage
 * Returns bytes used, available, and percent used
 * Estimates available as 5MB (typical quota) minus used
 */
function getQuotaInfo(): QuotaInfo {
  // Estimate quota as 5MB (5242880 bytes) — typical for localStorage
  const ESTIMATED_TOTAL_QUOTA = 5242880

  // Calculate used space: only count the value, not the key
  const value = localStorage.getItem(STORAGE_KEY)
  // Rough estimate: UTF-16 encoding means 1 char ≈ 2 bytes (plus overhead)
  const used = value ? value.length * 2 : 0

  const available = Math.max(0, ESTIMATED_TOTAL_QUOTA - used)
  const percentUsed = Math.min(100, (used / ESTIMATED_TOTAL_QUOTA) * 100)

  return {
    used,
    available,
    percentUsed,
  }
}

/**
 * Check for corruption in localStorage wallet
 * Attempts recovery from backup key if main is corrupted
 * Returns detailed status for error handling
 */
function checkCorruption(): CorruptionCheck {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)

    // No wallet stored is not corruption
    if (!stored) {
      return { corrupted: false }
    }

    // Try to parse and validate
    const parsed = JSON.parse(stored) as unknown
    if (isValidWallet(parsed)) {
      return { corrupted: false }
    }

    // Main wallet is corrupted, try to recover from backup
    const backupStored = localStorage.getItem(BACKUP_KEY)
    if (backupStored) {
      try {
        const backupParsed = JSON.parse(backupStored) as unknown
        if (isValidWallet(backupParsed)) {
          return {
            corrupted: true,
            recovered: backupParsed,
            error: 'Main wallet corrupted, recovered from backup',
          }
        }
      } catch {
        // Backup is also invalid, continue to total loss error
      }
    }

    // Total loss
    return {
      corrupted: true,
      error: 'Wallet data corrupted and no valid backup found. Please manually export any important data.',
    }
  } catch (err) {
    // JSON parse error or other issue
    const backupStored = localStorage.getItem(BACKUP_KEY)
    if (backupStored) {
      try {
        const backupParsed = JSON.parse(backupStored) as unknown
        if (isValidWallet(backupParsed)) {
          return {
            corrupted: true,
            recovered: backupParsed,
            error: 'Main wallet corrupted, recovered from backup',
          }
        }
      } catch {
        // Backup is also invalid
      }
    }

    return {
      corrupted: true,
      error: `Failed to read wallet: ${err instanceof Error ? err.message : 'Unknown error'}`,
    }
  }
}

/**
 * Public API: walletStorage
 */
export const walletStorage = {
  read,
  write,
  clear,
  getQuotaInfo,
  checkCorruption,
} as const
