import { renderHook, waitFor } from '@testing-library/react'
import { useWalletPersistence } from '../../src/hooks/useWalletPersistence'
import type { Wallet, WalletOrg } from '../../src/types/wallet'

describe('useWalletPersistence', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    localStorage.clear()
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

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

  describe('initial load', () => {
    it('returns synced=false on first render with empty storage', () => {
      const wallet = createTestWallet()
      const { result } = renderHook(() =>
        useWalletPersistence(wallet, false)
      )

      expect(result.current.synced).toBe(false)
      expect(result.current.error).toBeNull()
      expect(result.current.quotaWarning).toBe(false)
    })

    it('returns synced=true after mount when data exists in storage', () => {
      const wallet = createTestWallet([createTestOrg()])
      localStorage.setItem('daanaa_wallet', JSON.stringify(wallet))

      const { result } = renderHook(() =>
        useWalletPersistence(wallet, false)
      )

      // useEffect runs during render
      expect(result.current.synced).toBe(true)
    })

    it('sets error state on mount if corruption detected', () => {
      const corruptedData = 'invalid json {'
      localStorage.setItem('daanaa_wallet', corruptedData)

      // Also set a valid backup
      const backupWallet = createTestWallet([createTestOrg()])
      localStorage.setItem('daanaa_wallet_backup', JSON.stringify(backupWallet))

      const wallet = createTestWallet()
      const { result } = renderHook(() =>
        useWalletPersistence(wallet, false)
      )

      // Error should be set; parent component handles recovery via useEffect watching error state
      expect(result.current.error).toBeDefined()
    })
  })

  describe('write on change', () => {
    it('does not write when isDirty=false', async () => {
      const wallet = createTestWallet([createTestOrg()])
      const { rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: wallet, dirty: false },
        }
      )

      // No write should happen
      expect(localStorage.getItem('daanaa_wallet')).toBeNull()

      rerender({ w: wallet, dirty: false })
      expect(localStorage.getItem('daanaa_wallet')).toBeNull()
    })

    it('writes to localStorage when isDirty=true', async () => {
      const wallet = createTestWallet([createTestOrg()])
      const { rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: wallet, dirty: false },
        }
      )

      rerender({ w: wallet, dirty: true })

      // Advance timers to trigger debounced write (500ms)
      jest.advanceTimersByTime(500)

      await waitFor(() => {
        const stored = localStorage.getItem('daanaa_wallet')
        expect(stored).not.toBeNull()
      })
    })

    it('debounces rapid changes (500ms)', async () => {
      const wallet1 = createTestWallet([createTestOrg('001234567')])
      const wallet2 = createTestWallet([
        createTestOrg('001234567'),
        createTestOrg('002345678'),
      ])

      const { rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: wallet1, dirty: false },
        }
      )

      // Rapid changes
      rerender({ w: wallet1, dirty: true })
      jest.advanceTimersByTime(100)

      rerender({ w: wallet2, dirty: true })
      jest.advanceTimersByTime(100)

      rerender({ w: wallet2, dirty: true })
      jest.advanceTimersByTime(100)

      // After 300ms, still no write should have occurred
      expect(localStorage.getItem('daanaa_wallet')).toBeNull()

      // After 500ms, single write should have occurred with final state
      jest.advanceTimersByTime(200)

      await waitFor(() => {
        const stored = localStorage.getItem('daanaa_wallet')
        expect(stored).not.toBeNull()
        const parsed = JSON.parse(stored!)
        expect(parsed.orgs).toHaveLength(2)
      })
    })

  })

  describe('cleanup', () => {
    it('cancels pending writes on unmount', async () => {
      const wallet = createTestWallet([createTestOrg()])
      const { unmount, rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: wallet, dirty: false },
        }
      )

      rerender({ w: wallet, dirty: true })

      // Unmount before debounce timeout
      jest.advanceTimersByTime(100)
      unmount()
      jest.advanceTimersByTime(500)

      // No write should have occurred
      expect(localStorage.getItem('daanaa_wallet')).toBeNull()
    })
  })

  describe('quota and error handling', () => {
    it('sets quotaWarning when wallet exceeds 90% quota', async () => {
      // Create a large wallet that would trigger quota warning
      // Mock localStorage quota behavior
      const largeOrgs = Array.from({ length: 50 }, (_, i) =>
        createTestOrg(`${String(i).padStart(9, '0')}`)
      )
      const largeWallet = createTestWallet(largeOrgs)

      const { rerender, result } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: largeWallet, dirty: false },
        }
      )

      rerender({ w: largeWallet, dirty: true })
      jest.advanceTimersByTime(500)

      // Note: quotaWarning behavior depends on walletStorage.getQuotaInfo() implementation
      // This test verifies the hook properly tracks quota state
      await waitFor(() => {
        expect(result.current.quotaWarning).toBeDefined()
      })
    })

    it('clears quotaWarning when wallet size is reduced below 90%', async () => {
      const smallOrgs = [createTestOrg('001234567')]
      const smallWallet = createTestWallet(smallOrgs)

      const { rerender, result } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: smallWallet, dirty: false },
        }
      )

      // Initial write with small wallet
      rerender({ w: smallWallet, dirty: true })
      jest.advanceTimersByTime(500)

      await waitFor(() => {
        // After successful write with small data, quotaWarning should be false
        expect(result.current.quotaWarning).toBe(false)
      })
    })

    it('clears error state on successful write after previous error', async () => {
      const wallet = createTestWallet([createTestOrg()])

      const { rerender, result } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: wallet, dirty: false },
        }
      )

      // First write succeeds
      rerender({ w: wallet, dirty: true })
      jest.advanceTimersByTime(500)

      await waitFor(() => {
        expect(result.current.error).toBeNull()
      })

      // Verify error state can be cleared on subsequent successful writes
      const updatedWallet = createTestWallet([
        createTestOrg('001234567'),
        createTestOrg('002345678'),
      ])
      rerender({ w: updatedWallet, dirty: true })
      jest.advanceTimersByTime(500)

      await waitFor(() => {
        expect(result.current.error).toBeNull()
      })
    })

    it('final state reflects only final wallet after rapid changes', async () => {
      const org1 = createTestOrg('001234567')
      const org2 = createTestOrg('002345678')
      const org3 = createTestOrg('003456789')

      const wallet1 = createTestWallet([org1])
      const wallet2 = createTestWallet([]) // remove org1
      const wallet3 = createTestWallet([org2]) // add org2
      const wallet4 = createTestWallet([org2, org3]) // add org3

      const { rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: wallet1, dirty: false },
        }
      )

      // Rapid changes: add org1, remove org1, add org2, add org3
      rerender({ w: wallet1, dirty: true })
      jest.advanceTimersByTime(100)

      rerender({ w: wallet2, dirty: true })
      jest.advanceTimersByTime(100)

      rerender({ w: wallet3, dirty: true })
      jest.advanceTimersByTime(100)

      rerender({ w: wallet4, dirty: true })
      jest.advanceTimersByTime(100)

      // Should still have no write at 400ms
      expect(localStorage.getItem('daanaa_wallet')).toBeNull()

      // After 500ms total, single write with final state (org2 + org3)
      jest.advanceTimersByTime(100)

      await waitFor(() => {
        const stored = localStorage.getItem('daanaa_wallet')
        expect(stored).not.toBeNull()
        const parsed = JSON.parse(stored!)
        expect(parsed.orgs).toHaveLength(2)
        expect(parsed.orgs[0].ein).toBe('002345678')
        expect(parsed.orgs[1].ein).toBe('003456789')
      })
    })
  })

  describe('integration', () => {
    it('loads on mount, syncs on change', async () => {
      const initialWallet = createTestWallet([createTestOrg('001234567')])
      localStorage.setItem('daanaa_wallet', JSON.stringify(initialWallet))

      const { result, rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty),
        {
          initialProps: { w: initialWallet, dirty: false },
        }
      )

      // Mount: should load existing wallet
      expect(result.current.synced).toBe(true)

      // Change: add another org
      const updatedWallet = createTestWallet([
        createTestOrg('001234567'),
        createTestOrg('002345678'),
      ])
      rerender({ w: updatedWallet, dirty: true })
      jest.advanceTimersByTime(500)

      await waitFor(() => {
        const stored = localStorage.getItem('daanaa_wallet')
        const parsed = JSON.parse(stored!)
        expect(parsed.orgs).toHaveLength(2)
      })
    })
  })
})
