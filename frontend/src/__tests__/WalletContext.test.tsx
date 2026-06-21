import React from 'react'
import { render, act, screen } from '@testing-library/react'
import { WalletProvider, useWallet } from '../contexts/WalletContext'
import type { WalletEntry } from '../types/wallet'

// Mock env module to avoid import.meta.env in jest (CommonJS context)
jest.mock('../utils/env', () => ({
  getApiBase: () => 'http://localhost:5000',
}))

// Mock crypto module — we test WalletContext logic, not crypto primitives
jest.mock('../utils/wallet.crypto', () => ({
  encryptWallet: jest.fn().mockResolvedValue({ ciphertext: 'ct', iv: 'iv' }),
  decryptWallet: jest.fn().mockResolvedValue([]),
  deriveAll: jest.fn().mockResolvedValue({ encKey: {} as CryptoKey, keyHash: 'a'.repeat(64) }),
  deriveRawKeyBytes: jest.fn().mockResolvedValue(new Uint8Array(32).fill(1)),
  importKeyFromBytes: jest.fn().mockResolvedValue({} as CryptoKey),
}))

// Mock fetch (WalletContext calls /api/wallet/sync and /api/wallet/init)
global.fetch = jest.fn().mockResolvedValue({
  ok: false,
  json: jest.fn().mockResolvedValue({}),
} as any)

function Probe({ onMount }: { onMount: (w: ReturnType<typeof useWallet>) => void }) {
  const wallet = useWallet()
  onMount(wallet) // called on every render so ctx always reflects current state
  return null
}

describe('WalletContext', () => {
  afterEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  it('starts with empty entries', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.entries).toEqual([])
  })

  it('addEntry adds a WalletEntry by EIN only', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => {
      ctx.addEntry('123456789')
    })
    expect(ctx.entries).toHaveLength(1)
    expect(ctx.entries[0].ein).toBe('123456789')
    // Must NOT contain org snapshot fields
    expect((ctx.entries[0] as any).name).toBeUndefined()
    expect((ctx.entries[0] as any).mission).toBeUndefined()
  })

  it('removeEntry removes by EIN', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => { ctx.addEntry('123456789') })
    await act(async () => { ctx.removeEntry('123456789') })
    expect(ctx.entries).toHaveLength(0)
  })

  it('isInWallet returns false for unknown EIN', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.isInWallet('999999999')).toBe(false)
  })

  it('addEntry rejects malformed EIN', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => { ctx.addEntry('bad') })
    expect(ctx.entries).toHaveLength(0)
  })

  it('isUnlocked is false initially', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.isUnlocked).toBe(false)
  })
})

describe('legacy wallet migration', () => {
  const legacyWallet = {
    version: 1,
    lastUpdated: Date.now(),
    orgs: [
      {
        ein: '123456789',
        bookmarkedAt: 1718000000000,
        name: 'Old Org Name',
        mission: 'Old mission text',
        location: 'NYC',
        cause: ['education'],
        merit_score_v5: 75,
        merit_health_signal_v5: 'HEALTHY',
        is_hidden_gem: false,
        givingIntent: { type: 'giving', addedAt: 1718000000000, amount: 100 },
      },
    ],
    syncedWithServer: false,
  }

  beforeEach(() => {
    localStorage.setItem('daanaa_wallet', JSON.stringify(legacyWallet))
  })
  afterEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  it('detects legacy wallet and exposes migrationData', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.migrationData).toHaveLength(1)
    expect(ctx.migrationData[0].ein).toBe('123456789')
    expect((ctx.migrationData[0] as any).name).toBeUndefined()
  })

  it('migrationData preserves givingIntent', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.migrationData[0].givingIntent?.type).toBe('giving')
    expect(ctx.migrationData[0].givingIntent?.amount).toBe(100)
  })

  it('applyMigration merges entries and clears legacy key', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => { ctx.applyMigration() })
    expect(ctx.entries).toHaveLength(1)
    expect(ctx.entries[0].ein).toBe('123456789')
    expect(ctx.entries[0].givingIntent?.amount).toBe(100)
    expect(localStorage.getItem('daanaa_wallet')).toBeNull()
    expect(ctx.migrationData).toBeNull()
  })

  it('dismissMigration removes legacy key without importing entries', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => { ctx.dismissMigration() })
    expect(ctx.entries).toHaveLength(0)
    expect(localStorage.getItem('daanaa_wallet')).toBeNull()
    expect(ctx.migrationData).toBeNull()
  })
})
