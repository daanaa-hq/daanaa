import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { WalletProvider, useWallet } from '../../src/contexts/WalletContext'
import type { WalletOrg, GivingIntent } from '../../src/types/wallet'

const STORAGE_KEY = 'daanaa_wallet'

const mockOrg: WalletOrg = {
  ein: '123456789',
  name: 'Test Org',
  mission: 'Testing nonprofits',
  location: 'Austin, TX',
  cause: ['education'],
  merit_score_v5: 75,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
}

const mockIntent: GivingIntent = {
  type: 'giving',
  status: 'interested',
  amount: 250,
  addedAt: Date.now(),
}

let capturedWalletContext: ReturnType<typeof useWallet> | null = null

function TestComponent() {
  const wallet = useWallet()
  React.useEffect(() => {
    capturedWalletContext = wallet
  }, [wallet])
  return (
    <div>
      <div data-testid="org-count">{wallet.wallet.orgs.length}</div>
      <div data-testid="last-updated">{wallet.wallet.lastUpdated}</div>
    </div>
  )
}

describe('WalletContext', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
    capturedWalletContext = null
  })

  describe('WalletProvider', () => {
    it('renders without crashing', () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )
      expect(screen.getByTestId('org-count')).toBeInTheDocument()
    })

    it('throws error when useWallet is used outside provider', () => {
      function BadComponent() {
        useWallet()
        return <div>Should not render</div>
      }

      expect(() => {
        render(<BadComponent />)
      }).toThrow('useWallet must be used within WalletProvider')
    })

    it('initializes with empty wallet', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      expect(capturedWalletContext!.wallet.orgs).toHaveLength(0)
      expect(capturedWalletContext!.wallet.version).toBe(1)
      expect(capturedWalletContext!.wallet.syncedWithServer).toBe(false)
    })
  })

  describe('addOrg', () => {
    it('adds a new org to the wallet', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })
    })

    it('prevents duplicate orgs', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)
      capturedWalletContext!.addOrg(mockOrg) // Same EIN

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })
    })

    it('rejects invalid org data silently', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      const invalidOrg = { ein: '123', name: 'Bad Org' } as any
      capturedWalletContext!.addOrg(invalidOrg)

      // Should not add the invalid org
      expect(screen.getByTestId('org-count')).toHaveTextContent('0')
    })

    it('updates lastUpdated timestamp on add', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      const initialUpdated = capturedWalletContext!.wallet.lastUpdated

      // Wait a bit to ensure timestamp changes
      await new Promise(resolve => setTimeout(resolve, 10))

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        const newUpdated = capturedWalletContext!.wallet.lastUpdated
        expect(newUpdated).toBeGreaterThan(initialUpdated)
      })
    })
  })

  describe('removeOrg', () => {
    it('removes an org from the wallet', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })

      capturedWalletContext!.removeOrg(mockOrg.ein)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('0')
      })
    })

    it('does nothing if org not found', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })

      capturedWalletContext!.removeOrg('999999999') // Wrong EIN

      // Should still have 1 org
      expect(screen.getByTestId('org-count')).toHaveTextContent('1')
    })

    it('updates lastUpdated on remove', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })

      const initialUpdated = capturedWalletContext!.wallet.lastUpdated

      await new Promise(resolve => setTimeout(resolve, 10))

      capturedWalletContext!.removeOrg(mockOrg.ein)

      await waitFor(() => {
        const newUpdated = capturedWalletContext!.wallet.lastUpdated
        expect(newUpdated).toBeGreaterThan(initialUpdated)
      })
    })
  })

  describe('updateIntent', () => {
    it('adds intent to existing org', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })

      capturedWalletContext!.updateIntent(mockOrg.ein, mockIntent)

      await waitFor(() => {
        const intent = capturedWalletContext!.getIntent(mockOrg.ein)
        expect(intent).toEqual(mockIntent)
      })
    })

    it('updates existing intent', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg({ ...mockOrg, givingIntent: mockIntent })

      const newIntent: GivingIntent = {
        ...mockIntent,
        amount: 500,
      }

      capturedWalletContext!.updateIntent(mockOrg.ein, newIntent)

      await waitFor(() => {
        const intent = capturedWalletContext!.getIntent(mockOrg.ein)
        expect(intent?.amount).toBe(500)
      })
    })

    it('rejects invalid intent data silently', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      const invalidIntent = { type: 'invalid', status: 'interested', addedAt: Date.now() } as any
      capturedWalletContext!.updateIntent(mockOrg.ein, invalidIntent)

      // Intent should not be updated
      const intent = capturedWalletContext!.getIntent(mockOrg.ein)
      expect(intent).toBeUndefined()
    })

    it('does nothing if org not found', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      // This should silently do nothing
      capturedWalletContext!.updateIntent('999999999', mockIntent)

      expect(capturedWalletContext!.getIntent('999999999')).toBeUndefined()
    })

    it('updates lastUpdated on intent change', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(screen.getByTestId('org-count')).toHaveTextContent('1')
      })

      const initialUpdated = capturedWalletContext!.wallet.lastUpdated

      await new Promise(resolve => setTimeout(resolve, 10))

      capturedWalletContext!.updateIntent(mockOrg.ein, mockIntent)

      await waitFor(() => {
        const newUpdated = capturedWalletContext!.wallet.lastUpdated
        expect(newUpdated).toBeGreaterThan(initialUpdated)
      })
    })
  })

  describe('isInWallet', () => {
    it('returns true for org in wallet', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        expect(capturedWalletContext!.isInWallet(mockOrg.ein)).toBe(true)
      })
    })

    it('returns false for org not in wallet', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      expect(capturedWalletContext!.isInWallet('999999999')).toBe(false)
    })
  })

  describe('getIntent', () => {
    it('returns intent for org with intent', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg({ ...mockOrg, givingIntent: mockIntent })

      await waitFor(() => {
        const intent = capturedWalletContext!.getIntent(mockOrg.ein)
        expect(intent).toEqual(mockIntent)
      })
    })

    it('returns undefined for org without intent', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        const intent = capturedWalletContext!.getIntent(mockOrg.ein)
        expect(intent).toBeUndefined()
      })
    })

    it('returns undefined for org not in wallet', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      expect(capturedWalletContext!.getIntent('999999999')).toBeUndefined()
    })
  })

  describe('localStorage persistence', () => {
    it('persists wallet to localStorage on change', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)

      await waitFor(() => {
        const stored = localStorage.getItem(STORAGE_KEY)
        expect(stored).toBeTruthy()
        const parsed = JSON.parse(stored!)
        expect(parsed.orgs).toHaveLength(1)
        expect(parsed.orgs[0].ein).toBe(mockOrg.ein)
      })
    })

    it('hydrates wallet from localStorage on mount', async () => {
      const wallet = {
        version: 1,
        lastUpdated: Date.now(),
        orgs: [mockOrg],
        syncedWithServer: false,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(wallet))

      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(1)
        expect(capturedWalletContext!.wallet.orgs[0].ein).toBe(mockOrg.ein)
      })
    })

    it('recovers from corrupted localStorage data', async () => {
      localStorage.setItem(STORAGE_KEY, 'invalid json {')

      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(0)
      })
    })

    it('recovers from invalid wallet schema in localStorage', async () => {
      const invalidWallet = {
        version: 2, // Wrong version
        orgs: [],
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(invalidWallet))

      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(0)
      })
    })
  })

  describe('syncToServer', () => {
    it('marks wallet as synced and stores googleEmail', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      expect(capturedWalletContext!.wallet.syncedWithServer).toBe(false)

      await capturedWalletContext!.syncToServer('user@example.com', 'token123')

      await waitFor(() => {
        expect(capturedWalletContext!.wallet.syncedWithServer).toBe(true)
        expect(capturedWalletContext!.wallet.googleEmail).toBe('user@example.com')
      })
    })

    it('throws error if email or token missing', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      await expect(capturedWalletContext!.syncToServer('', 'token')).rejects.toThrow()
      await expect(capturedWalletContext!.syncToServer('user@example.com', '')).rejects.toThrow()
    })
  })

  describe('logoutAndClearSync', () => {
    it('clears sync state but keeps orgs', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      capturedWalletContext!.addOrg(mockOrg)
      await capturedWalletContext!.syncToServer('user@example.com', 'token123')

      await waitFor(() => {
        expect(capturedWalletContext!.wallet.syncedWithServer).toBe(true)
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(1)
      })

      capturedWalletContext!.logoutAndClearSync()

      await waitFor(() => {
        expect(capturedWalletContext!.wallet.syncedWithServer).toBe(false)
        expect(capturedWalletContext!.wallet.googleEmail).toBeUndefined()
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(1)
      })
    })
  })

  describe('complex workflows', () => {
    it('handles add, update intent, remove flow', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      // Add org
      capturedWalletContext!.addOrg(mockOrg)
      await waitFor(() => {
        expect(capturedWalletContext!.isInWallet(mockOrg.ein)).toBe(true)
      })

      // Add intent
      capturedWalletContext!.updateIntent(mockOrg.ein, mockIntent)
      await waitFor(() => {
        expect(capturedWalletContext!.getIntent(mockOrg.ein)).toEqual(mockIntent)
      })

      // Remove org
      capturedWalletContext!.removeOrg(mockOrg.ein)
      await waitFor(() => {
        expect(capturedWalletContext!.isInWallet(mockOrg.ein)).toBe(false)
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(0)
      })
    })

    it('handles multiple orgs independently', async () => {
      render(
        <WalletProvider>
          <TestComponent />
        </WalletProvider>
      )

      await waitFor(() => {
        expect(capturedWalletContext).not.toBeNull()
      })

      const org2 = { ...mockOrg, ein: '987654321', name: 'Another Org' }

      capturedWalletContext!.addOrg(mockOrg)
      capturedWalletContext!.addOrg(org2)

      await waitFor(() => {
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(2)
      })

      const intent1: GivingIntent = {
        type: 'giving',
        status: 'interested',
        amount: 250,
        addedAt: Date.now(),
      }

      const intent2: GivingIntent = {
        type: 'volunteer',
        status: 'interested',
        hours: 5,
        addedAt: Date.now(),
      }

      capturedWalletContext!.updateIntent(mockOrg.ein, intent1)
      capturedWalletContext!.updateIntent(org2.ein, intent2)

      await waitFor(() => {
        expect(capturedWalletContext!.getIntent(mockOrg.ein)).toEqual(intent1)
        expect(capturedWalletContext!.getIntent(org2.ein)).toEqual(intent2)
      })

      capturedWalletContext!.removeOrg(mockOrg.ein)

      await waitFor(() => {
        expect(capturedWalletContext!.wallet.orgs).toHaveLength(1)
        expect(capturedWalletContext!.isInWallet(org2.ein)).toBe(true)
        expect(capturedWalletContext!.isInWallet(mockOrg.ein)).toBe(false)
      })
    })
  })
})
