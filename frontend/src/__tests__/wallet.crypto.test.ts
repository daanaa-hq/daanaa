// Jest + jsdom: SubtleCrypto is available in jsdom 20+
import {
  deriveAll,
  encryptWallet,
  decryptWallet,
  generatePassphrase,
} from '../utils/wallet.crypto'
import type { WalletEntry } from '../types/wallet'
import wordlistJson from '../../public/bip39-english.json'

const TEST_PASSPHRASE = 'correct horse battery staple'
const TEST_SALT = new Uint8Array(16).fill(0)

describe('generatePassphrase', () => {
  it('returns exactly 4 words', async () => {
    const phrase = await generatePassphrase()
    expect(phrase.split(' ')).toHaveLength(4)
  })

  it('all words come from BIP39 wordlist', async () => {
    const phrase = await generatePassphrase()
    const wordlist = wordlistJson as string[]
    for (const word of phrase.split(' ')) {
      expect(wordlist).toContain(word)
    }
  })

  it('generates different phrases each call', async () => {
    const p1 = await generatePassphrase()
    const p2 = await generatePassphrase()
    expect(p1).not.toBe(p2)
  })
})

describe('deriveAll', () => {
  it('returns encKey and keyHash', async () => {
    const { encKey, keyHash } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    expect(encKey).toBeDefined()
    expect(keyHash).toMatch(/^[0-9a-f]{64}$/)
  })

  it('keyHash is deterministic for same passphrase+salt', async () => {
    const { keyHash: h1 } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { keyHash: h2 } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    expect(h1).toBe(h2)
  })

  it('different passphrase → different keyHash', async () => {
    const { keyHash: h1 } = await deriveAll('correct horse battery staple', TEST_SALT)
    const { keyHash: h2 } = await deriveAll('wrong horse battery staple', TEST_SALT)
    expect(h1).not.toBe(h2)
  })

  it('encKey is non-extractable (security invariant)', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    await expect(
      crypto.subtle.exportKey('raw', encKey)
    ).rejects.toThrow()
  })
})

describe('encrypt / decrypt round-trip', () => {
  const entries: WalletEntry[] = [
    { ein: '123456789', bookmarkedAt: 1718000000000, givingIntent: { type: 'giving', amount: 100, addedAt: 1718000001000 } },
    { ein: '987654321', bookmarkedAt: 1718000002000 },
  ]

  it('round-trips entries through encrypt → decrypt', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { ciphertext, iv } = await encryptWallet(entries, encKey)
    const decrypted = await decryptWallet(ciphertext, iv, encKey)
    expect(decrypted).toEqual(entries)
  })

  it('each encryption produces different iv', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { iv: iv1 } = await encryptWallet(entries, encKey)
    const { iv: iv2 } = await encryptWallet(entries, encKey)
    expect(iv1).not.toBe(iv2)
  })

  it('wrong key cannot decrypt', async () => {
    const { encKey: goodKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { encKey: badKey } = await deriveAll('wrong phrase here xx', TEST_SALT)
    const { ciphertext, iv } = await encryptWallet(entries, goodKey)
    await expect(decryptWallet(ciphertext, iv, badKey)).rejects.toThrow()
  })

  it('tampered ciphertext fails decryption (AES-GCM authentication)', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { ciphertext, iv } = await encryptWallet(entries, encKey)
    const bytes = Uint8Array.from(atob(ciphertext), c => c.charCodeAt(0))
    bytes[0] ^= 0xFF
    const tampered = btoa(String.fromCharCode(...bytes))
    await expect(decryptWallet(tampered, iv, encKey)).rejects.toThrow()
  })
})
