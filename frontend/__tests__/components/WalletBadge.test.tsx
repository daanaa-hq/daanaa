import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import WalletBadge from '../../src/components/WalletBadge'
import { WalletContext } from '../../src/contexts/WalletContext'
import type { WalletContextType, WalletOrg } from '../../src/types/wallet'

const mockOrgWithGiving = (ein: string): WalletOrg => ({
  ein,
  name: 'Org with Giving',
  mission: 'Mission',
  location: 'Austin, TX',
  cause: ['environment'],
  merit_score_v5: 78,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
  givingIntent: {
    type: 'giving',
    status: 'interested',
    amount: 250,
    addedAt: Date.now(),
  },
})

const mockOrgWithVolunteer = (ein: string): WalletOrg => ({
  ein,
  name: 'Org with Volunteer',
  mission: 'Mission',
  location: 'Portland, OR',
  cause: ['community'],
  merit_score_v5: 62,
  merit_health_signal_v5: 'STABLE',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
  givingIntent: {
    type: 'volunteer',
    status: 'interested',
    hours: 5,
    addedAt: Date.now(),
  },
})

const mockOrgWithBoard = (ein: string): WalletOrg => ({
  ein,
  name: 'Org with Board',
  mission: 'Mission',
  location: 'New York, NY',
  cause: ['capacity-building'],
  merit_score_v5: 85,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
  givingIntent: {
    type: 'board',
    status: 'interested',
    addedAt: Date.now(),
  },
})

const mockOrgWithoutIntent = (ein: string): WalletOrg => ({
  ein,
  name: 'Org without Intent',
  mission: 'Mission',
  location: 'Boston, MA',
  cause: ['education'],
  merit_score_v5: 70,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: true,
  bookmarkedAt: Date.now(),
})

describe('WalletBadge', () => {
  const mockWalletContextValue = (orgs: WalletOrg[]): WalletContextType => ({
    wallet: {
      version: 1,
      lastUpdated: Date.now(),
      orgs,
      syncedWithServer: false,
    },
    addOrg: jest.fn(),
    removeOrg: jest.fn(),
    updateIntent: jest.fn(),
    isInWallet: jest.fn(),
    getIntent: jest.fn(),
    syncToServer: jest.fn(),
    logoutAndClearSync: jest.fn(),
  })

  const renderWithContext = (
    component: React.ReactElement,
    orgs: WalletOrg[] = []
  ) => {
    return render(
      <BrowserRouter>
        <WalletContext.Provider value={mockWalletContextValue(orgs)}>
          {component}
        </WalletContext.Provider>
      </BrowserRouter>
    )
  }

  describe('inline style', () => {
    it('renders inline count when orgs in wallet', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      renderWithContext(<WalletBadge style="inline" />, orgs)
      expect(screen.getByText(/2 organizations in wallet/i)).toBeInTheDocument()
    })

    it('shows "empty" when no orgs', () => {
      renderWithContext(<WalletBadge style="inline" />, [])
      expect(screen.getByText(/empty/i)).toBeInTheDocument()
    })

    it('shows singular "organization" with 1 org', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      renderWithContext(<WalletBadge style="inline" />, orgs)
      expect(screen.getByText(/1 organization in wallet/i)).toBeInTheDocument()
    })

    it('has correct aria-label for inline', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      renderWithContext(<WalletBadge style="inline" />, orgs)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '2 organizations in your wallet'
      )
    })
  })

  describe('badge style', () => {
    it('renders badge with count', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
        mockOrgWithBoard('333333333'),
      ]
      renderWithContext(<WalletBadge style="badge" />, orgs)
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('hides badge when 0 orgs', () => {
      const { container } = renderWithContext(<WalletBadge style="badge" />, [])
      expect(container.querySelector('span')).not.toBeInTheDocument()
    })

    it('has aria-label for badge', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      renderWithContext(<WalletBadge style="badge" />, orgs)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '2 organizations in your wallet'
      )
    })

    it('shows badge with red styling', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      const { container } = renderWithContext(
        <WalletBadge style="badge" />,
        orgs
      )
      const badge = container.querySelector('span')
      expect(badge).toHaveClass('bg-red-500')
    })
  })

  describe('pill style', () => {
    it('renders pill with count', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      renderWithContext(<WalletBadge style="pill" />, orgs)
      // Wallet and count are in separate spans, so check for both
      expect(screen.getByText('💾 Wallet')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('shows "0" in pill when empty', () => {
      renderWithContext(<WalletBadge style="pill" />, [])
      expect(screen.getByText('0')).toBeInTheDocument()
    })

    it('pill is clickable and navigates to wallet', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      const { container } = renderWithContext(
        <WalletBadge style="pill" />,
        orgs
      )
      const pill = container.querySelector('a')
      expect(pill).toHaveAttribute('href', '/giving-wallet')
    })

    it('has aria-label for pill', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      renderWithContext(<WalletBadge style="pill" />, orgs)
      expect(screen.getByRole('link')).toHaveAttribute(
        'aria-label',
        '2 organizations in your wallet'
      )
    })

    it('pill has proper styling', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      const { container } = renderWithContext(
        <WalletBadge style="pill" />,
        orgs
      )
      const pill = container.querySelector('a')
      expect(pill).toHaveClass('bg-orange-100')
      expect(pill).toHaveClass('rounded-full')
    })
  })

  describe('intent filtering', () => {
    it('filters by giving intent', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
        mockOrgWithBoard('333333333'),
      ]
      renderWithContext(<WalletBadge style="inline" intent="giving" />, orgs)
      expect(screen.getByText(/1 organization in wallet/i)).toBeInTheDocument()
    })

    it('filters by volunteer intent', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
        mockOrgWithBoard('333333333'),
      ]
      renderWithContext(
        <WalletBadge style="inline" intent="volunteer" />,
        orgs
      )
      expect(screen.getByText(/1 organization in wallet/i)).toBeInTheDocument()
    })

    it('filters by board intent', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
        mockOrgWithBoard('333333333'),
      ]
      renderWithContext(<WalletBadge style="inline" intent="board" />, orgs)
      expect(screen.getByText(/1 organization in wallet/i)).toBeInTheDocument()
    })

    it('excludes orgs without intent when filtering', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithoutIntent('444444444'),
      ]
      renderWithContext(<WalletBadge style="inline" intent="giving" />, orgs)
      expect(screen.getByText(/1 organization in wallet/i)).toBeInTheDocument()
    })

    it('shows empty when no orgs match intent filter', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
      ]
      renderWithContext(<WalletBadge style="inline" intent="board" />, orgs)
      expect(screen.getByText(/empty/i)).toBeInTheDocument()
    })

    it('filters correctly with badge style', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
        mockOrgWithBoard('333333333'),
      ]
      renderWithContext(<WalletBadge style="badge" intent="giving" />, orgs)
      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('filters correctly with pill style', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithVolunteer('222222222'),
        mockOrgWithBoard('333333333'),
      ]
      renderWithContext(<WalletBadge style="pill" intent="volunteer" />, orgs)
      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })

  describe('edge cases', () => {
    it('handles many orgs in wallet', () => {
      const orgs = Array.from({ length: 50 }, (_, i) =>
        mockOrgWithGiving(`${String(i + 1).padStart(9, '0')}`)
      )
      renderWithContext(<WalletBadge style="inline" />, orgs)
      expect(screen.getByText(/50 organizations in wallet/i)).toBeInTheDocument()
    })

    it('default style is inline', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      renderWithContext(<WalletBadge />, orgs)
      expect(screen.getByText(/1 organization in wallet/i)).toBeInTheDocument()
    })

    it('handles mixed intents correctly', () => {
      const orgs = [
        mockOrgWithGiving('111111111'),
        mockOrgWithGiving('222222222'),
        mockOrgWithVolunteer('333333333'),
        mockOrgWithBoard('444444444'),
        mockOrgWithoutIntent('555555555'),
      ]
      renderWithContext(<WalletBadge style="inline" />, orgs)
      expect(screen.getByText(/5 organizations in wallet/i)).toBeInTheDocument()

      renderWithContext(<WalletBadge style="inline" intent="giving" />, orgs)
      expect(screen.getByText(/2 organizations in wallet/i)).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('inline has aria-label', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      renderWithContext(<WalletBadge style="inline" />, orgs)
      const element = screen.getByRole('status')
      expect(element).toHaveAttribute('aria-label')
    })

    it('badge has role="status"', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      renderWithContext(<WalletBadge style="badge" />, orgs)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('pill is a focusable link', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      const { container } = renderWithContext(
        <WalletBadge style="pill" />,
        orgs
      )
      const link = container.querySelector('a')
      expect(link).toHaveAttribute('href')
      expect(link).toHaveAttribute('aria-label')
    })

    it('has high color contrast', () => {
      const orgs = [mockOrgWithGiving('111111111')]
      const { container } = renderWithContext(
        <WalletBadge style="badge" />,
        orgs
      )
      const badge = container.querySelector('span')
      expect(badge).toHaveClass('text-white')
    })
  })
})
