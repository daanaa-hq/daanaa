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
        useWalletPersistence(wallet, false, jest.fn())
      )

      expect(result.current.synced).toBe(false)
      expect(result.current.error).toBeNull()
      expect(result.current.quotaWarning).toBe(false)
    })

    it('returns synced=true after mount when data exists in storage', () => {
      const wallet = createTestWallet([createTestOrg()])
      localStorage.setItem('daanaa_wallet', JSON.stringify(wallet))

      const { result } = renderHook(() =>
        useWalletPersistence(wallet, false, jest.fn())
      )

      // useEffect runs during render
      expect(result.current.synced).toBe(true)
    })

    it('calls recovery callback on mount if corruption detected', () => {
      const recoveryCallback = jest.fn()
      const corruptedData = 'invalid json {'
      localStorage.setItem('daanaa_wallet', corruptedData)

      // Also set a valid backup
      const backupWallet = createTestWallet([createTestOrg()])
      localStorage.setItem('daanaa_wallet_backup', JSON.stringify(backupWallet))

      const wallet = createTestWallet()
      const { result } = renderHook(() =>
        useWalletPersistence(wallet, false, recoveryCallback)
      )

      expect(recoveryCallback).toHaveBeenCalledWith(backupWallet)
      expect(result.current.error).toBeDefined()
    })
  })

  describe('write on change', () => {
    it('does not write when isDirty=false', async () => {
      const wallet = createTestWallet([createTestOrg()])
      const { rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty, jest.fn()),
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
        ({ w, dirty }) => useWalletPersistence(w, dirty, jest.fn()),
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
        ({ w, dirty }) => useWalletPersistence(w, dirty, jest.fn()),
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
        ({ w, dirty }) => useWalletPersistence(w, dirty, jest.fn()),
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

  describe('integration', () => {
    it('loads on mount, syncs on change', async () => {
      const recoveryCallback = jest.fn()
      const initialWallet = createTestWallet([createTestOrg('001234567')])
      localStorage.setItem('daanaa_wallet', JSON.stringify(initialWallet))

      const { result, rerender } = renderHook(
        ({ w, dirty }) => useWalletPersistence(w, dirty, recoveryCallback),
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
