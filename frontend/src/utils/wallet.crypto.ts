// All native browser SubtleCrypto — zero imports.
// Design doc: ~/.gstack/projects/meritgiving/akbar-master-design-20260620-181500.md

import type { WalletEntry } from '../types/wallet'
import wordlistJson from '../../public/bip39-english.json'

const PBKDF2_ITERATIONS = 310_000

function getWordlist(): string[] {
  return wordlistJson as string[]
}

/**
 * Generate a 4-word BIP39 passphrase.
 * Entropy: 2048^4 = 2^44. Acceptable for giving-intent data.
 */
export async function generatePassphrase(): Promise<string> {
  const words = getWordlist()
  const indices = new Uint32Array(4)
  crypto.getRandomValues(indices)
  return Array.from(indices).map(i => words[i % 2048]).join(' ')
}

/**
 * Derive encryption key and server lookup token from passphrase + salt.
 *
 * PBKDF2 once → PRK → HKDF-Expand twice:
 *   "daanaa-wallet-key" → AES-GCM encryption key  (never leaves device)
 *   "daanaa-wallet-id"  → server lookup token (safe to send; cannot reverse to key)
 */
export async function deriveAll(
  passphrase: string,
  salt: Uint8Array
): Promise<{ encKey: CryptoKey; keyHash: string }> {
  const enc = new TextEncoder()

  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveBits']
  )
  const prkBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    keyMaterial, 256
  )
  const prk = await crypto.subtle.importKey('raw', prkBits, 'HKDF', false, ['deriveBits'])

  const encBits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc.encode('daanaa-wallet-key') },
    prk, 256
  )
  const encKey = await crypto.subtle.importKey(
    'raw', encBits, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  )

  const idBits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc.encode('daanaa-wallet-id') },
    prk, 256
  )
  const keyHash = Array.from(new Uint8Array(idBits))
    .map(b => b.toString(16).padStart(2, '0')).join('')

  return { encKey, keyHash }
}

/**
 * Encrypt wallet entries. Fresh IV on every call (AES-GCM requirement).
 */
export async function encryptWallet(
  entries: WalletEntry[],
  key: CryptoKey
): Promise<{ ciphertext: string; iv: string }> {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const plaintext = JSON.stringify({ entries, syncedAt: Date.now() })
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    new TextEncoder().encode(plaintext)
  )
  return {
    ciphertext: btoa(String.fromCharCode(...new Uint8Array(encrypted))),
    iv: btoa(String.fromCharCode(...iv)),
  }
}

/**
 * Decrypt wallet entries.
 * Throws if key is wrong, ciphertext tampered, or format invalid.
 */
export async function decryptWallet(
  ciphertext: string,
  iv: string,
  key: CryptoKey
): Promise<WalletEntry[]> {
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: Uint8Array.from(atob(iv), c => c.charCodeAt(0)) },
    key,
    Uint8Array.from(atob(ciphertext), c => c.charCodeAt(0))
  )
  const parsed = JSON.parse(new TextDecoder().decode(decrypted))
  return parsed.entries as WalletEntry[]
}

/**
 * Export raw AES key bytes for sessionStorage caching.
 * Re-derived from passphrase (CryptoKey is non-extractable, so we re-run HKDF).
 * Used only by WalletContext — not for general use.
 */
export async function deriveRawKeyBytes(
  passphrase: string,
  salt: Uint8Array
): Promise<Uint8Array> {
  const enc = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveBits']
  )
  const prkBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    keyMaterial, 256
  )
  const prk = await crypto.subtle.importKey('raw', prkBits, 'HKDF', false, ['deriveBits'])
  const encBits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc.encode('daanaa-wallet-key') },
    prk, 256
  )
  return new Uint8Array(encBits)
}

/**
 * Import raw key bytes back to a CryptoKey (non-extractable).
 * Used by WalletContext to restore session key from sessionStorage.
 */
export async function importKeyFromBytes(bytes: Uint8Array): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    'raw', bytes, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  )
}
