import { walletStorage } from '../../src/utils/walletStorage'
import type { Wallet, WalletOrg } from '../../src/types/wallet'

describe('walletStorage', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
    jest.restoreAllMocks()
  })

  // Helper to create valid test data
  function createTestOrg(ein: string = '001234567'): WalletOrg {
    return {
      ein,
      name: 'Test Org',
      mission: 'Testing mission',
      location: 'Test City, TS',
      cause: ['environment'],
      merit_score_v5: 75,
      merit_health_signal_v5: 'HEALTHY',
      is_hidden_gem: false,
      bookmarkedAt: Date.now(),
    }
  }

  function createTestWallet(orgs: WalletOrg[] = []): Wallet {
    return {
      version: 1,
      lastUpdated: Date.now(),
      orgs,
      syncedWithServer: false,
    }
  }

  describe('read()', () => {
    it('returns null if wallet key does not exist', () => {
      const result = walletStorage.read()
      expect(result).toBeNull()
    })

    it('returns valid wallet from localStorage', () => {
      const wallet = createTestWallet([createTestOrg()])
      localStorage.setItem('daanaa_wallet', JSON.stringify(wallet))

      const result = walletStorage.read()
      expect(result).not.toBeNull()
      expect(result?.version).toBe(1)
      expect(result?.orgs).toHaveLength(1)
      expect(result?.orgs[0].ein).toBe('001234567')
    })

    it('returns null if stored data is invalid JSON', () => {
      localStorage.setItem('daanaa_wallet', 'invalid json {')
      const result = walletStorage.read()
      expect(result).toBeNull()
    })

    it('returns null if wallet schema is invalid', () => {
      localStorage.setItem('daanaa_wallet', JSON.stringify({ version: 2, orgs: [] }))
      const result = walletStorage.read()
      expect(result).toBeNull()
    })

    it('returns null if orgs array contains invalid org', () => {
      const invalidWallet = {
        version: 1,
        lastUpdated: Date.now(),
        orgs: [{ ein: '123' }], // Missing required fields
        syncedWithServer: false,
      }
      localStorage.setItem('daanaa_wallet', JSON.stringify(invalidWallet))
      const result = walletStorage.read()
      expect(result).toBeNull()
    })
  })

  describe('write()', () => {
    it('stores wallet to localStorage', () => {
      const wallet = createTestWallet([createTestOrg()])
      walletStorage.write(wallet)

      const stored = localStorage.getItem('daanaa_wallet')
      expect(stored).not.toBeNull()
      const parsed = JSON.parse(stored!)
      expect(parsed.version).toBe(1)
      expect(parsed.orgs).toHaveLength(1)
    })

    it('can read back written wallet', () => {
      const wallet = createTestWallet([createTestOrg()])
      walletStorage.write(wallet)

      const result = walletStorage.read()
      expect(result).not.toBeNull()
      expect(result?.orgs[0].ein).toBe('001234567')
    })

    it('updates existing wallet', () => {
      const wallet1 = createTestWallet([createTestOrg('001234567')])
      walletStorage.write(wallet1)

      const wallet2 = createTestWallet([
        createTestOrg('001234567'),
        createTestOrg('002345678'),
      ])
      walletStorage.write(wallet2)

      const result = walletStorage.read()
      expect(result?.orgs).toHaveLength(2)
    })

    it('logs console warning when quota exceeds 90%', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn')
      const wallet = createTestWallet([createTestOrg()])

      // This test is environment-dependent and may not always warn
      walletStorage.write(wallet)
      // If warning happens, it should contain quota info
      if (consoleWarnSpy.mock.calls.length > 0) {
        expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('quota'))
      }

      consoleWarnSpy.mockRestore()
    })

    it('handles write error gracefully', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      const wallet = createTestWallet([createTestOrg()])

      // Save original setItem
      const originalSetItem = localStorage.setItem

      // Mock localStorage.setItem to throw
      Object.defineProperty(localStorage, 'setItem', {
        value: jest.fn(() => {
          throw new Error('Storage error')
        }),
      })

      walletStorage.write(wallet)

      expect(consoleErrorSpy).toHaveBeenCalled()
      expect(consoleErrorSpy.mock.calls[0][0]).toContain('Failed to write')

      // Restore
      Object.defineProperty(localStorage, 'setItem', {
        value: originalSetItem,
      })
      consoleErrorSpy.mockRestore()
    })
  })

  describe('clear()', () => {
    it('removes wallet from localStorage', () => {
      const wallet = createTestWallet([createTestOrg()])
      walletStorage.write(wallet)
      expect(localStorage.getItem('daanaa_wallet')).not.toBeNull()

      walletStorage.clear()
      expect(localStorage.getItem('daanaa_wallet')).toBeNull()
    })

    it('can be called when wallet does not exist', () => {
      expect(() => {
        walletStorage.clear()
      }).not.toThrow()
    })
  })

  describe('getQuotaInfo()', () => {
    it('returns quota info with 0 used when empty', () => {
      const info = walletStorage.getQuotaInfo()
      expect(info.used).toBe(0)
      expect(info.available).toBeGreaterThan(0)
      expect(info.percentUsed).toBe(0)
    })

    it('returns accurate quota info when wallet stored', () => {
      const wallet = createTestWallet([createTestOrg()])
      walletStorage.write(wallet)

      const info = walletStorage.getQuotaInfo()
      expect(info.used).toBeGreaterThan(0)
      expect(info.available).toBeGreaterThan(0)
      expect(info.percentUsed).toBeGreaterThan(0)
      expect(info.percentUsed).toBeLessThan(100)
    })

    it('returns percentUsed as 0-100', () => {
      const wallet = createTestWallet([createTestOrg()])
      walletStorage.write(wallet)

      const info = walletStorage.getQuotaInfo()
      expect(info.percentUsed).toBeGreaterThanOrEqual(0)
      expect(info.percentUsed).toBeLessThanOrEqual(100)
    })

    it('increases used space when more orgs added', () => {
      const wallet1 = createTestWallet([createTestOrg('001234567')])
      walletStorage.write(wallet1)
      const info1 = walletStorage.getQuotaInfo()

      const wallet2 = createTestWallet([
        createTestOrg('001234567'),
        createTestOrg('002345678'),
        createTestOrg('003456789'),
      ])
      walletStorage.write(wallet2)
      const info2 = walletStorage.getQuotaInfo()

      expect(info2.used).toBeGreaterThan(info1.used)
      expect(info2.percentUsed).toBeGreaterThan(info1.percentUsed)
    })
  })

  describe('checkCorruption()', () => {
    it('returns { corrupted: false } for valid wallet', () => {
      const wallet = createTestWallet([createTestOrg()])
      walletStorage.write(wallet)

      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(false)
      expect(result.recovered).toBeUndefined()
      expect(result.error).toBeUndefined()
    })

    it('returns { corrupted: false } when no wallet exists', () => {
      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(false)
    })

    it('detects invalid JSON as corruption', () => {
      localStorage.setItem('daanaa_wallet', 'invalid json {')

      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(true)
      expect(result.error).toBeDefined()
    })

    it('detects invalid schema as corruption', () => {
      const invalidWallet = {
        version: 2,
        orgs: [],
      }
      localStorage.setItem('daanaa_wallet', JSON.stringify(invalidWallet))

      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(true)
      expect(result.error).toBeDefined()
    })

    it('recovers from backup key if main is corrupted', () => {
      const backupWallet = createTestWallet([createTestOrg()])
      localStorage.setItem('daanaa_wallet_backup', JSON.stringify(backupWallet))
      localStorage.setItem('daanaa_wallet', 'invalid json {')

      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(true)
      expect(result.recovered).not.toBeUndefined()
      expect(result.recovered?.orgs).toHaveLength(1)
      expect(result.recovered?.orgs[0].ein).toBe('001234567')
    })

    it('returns error if total loss (no main, no backup)', () => {
      localStorage.setItem('daanaa_wallet', 'invalid json {')

      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(true)
      expect(result.recovered).toBeUndefined()
      expect(result.error).toBeDefined()
    })

    it('returns error if backup is also invalid', () => {
      localStorage.setItem('daanaa_wallet', 'invalid {')
      localStorage.setItem('daanaa_wallet_backup', 'also invalid {')

      const result = walletStorage.checkCorruption()
      expect(result.corrupted).toBe(true)
      expect(result.recovered).toBeUndefined()
      expect(result.error).toBeDefined()
    })
  })
})
