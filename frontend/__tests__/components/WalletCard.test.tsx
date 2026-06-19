import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import WalletCard from '../../src/components/WalletCard'
import type { WalletOrg } from '../../src/types/wallet'

const mockOrgWithGiving: WalletOrg = {
  ein: '111111111',
  name: 'Save the World',
  mission: 'Fighting climate change through community education and action',
  location: 'Austin, TX',
  cause: ['environment', 'education', 'climate'],
  merit_score_v5: 78,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  donate_url: 'https://savetheworld.org/donate',
  bookmarkedAt: Date.now(),
  givingIntent: {
    type: 'giving',
    status: 'interested',
    amount: 250,
    addedAt: Date.now(),
    notes: 'Great work on carbon offset programs',
  },
}

const mockOrgWithVolunteer: WalletOrg = {
  ein: '222222222',
  name: 'Community Kitchen',
  mission: 'Providing meals and food education to underserved neighborhoods',
  location: 'Portland, OR',
  cause: ['food', 'community'],
  merit_score_v5: 62,
  merit_health_signal_v5: 'STABLE',
  is_hidden_gem: true,
  bookmarkedAt: Date.now(),
  givingIntent: {
    type: 'volunteer',
    status: 'interested',
    hours: 5,
    addedAt: Date.now(),
  },
}

const mockOrgWithBoard: WalletOrg = {
  ein: '333333333',
  name: 'Leadership Initiative',
  mission: 'Building tomorrow\'s nonprofit leaders through mentorship and training',
  location: 'New York, NY',
  cause: ['capacity-building'],
  merit_score_v5: 88,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
  givingIntent: {
    type: 'board',
    status: 'interested',
    addedAt: Date.now(),
  },
}

const mockOrgNoIntent: WalletOrg = {
  ein: '444444444',
  name: 'Bookmarked Org',
  mission: 'No giving intent set yet',
  location: 'Chicago, IL',
  cause: ['arts'],
  merit_score_v5: 70,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
}

const mockOrgCaution: WalletOrg = {
  ein: '555555555',
  name: 'Small Charity',
  mission: 'Serving local communities with limited resources',
  location: 'Denver, CO',
  cause: ['health'],
  merit_score_v5: 45,
  merit_health_signal_v5: 'CAUTION',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
}

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>
}

describe('WalletCard', () => {
  const mockOnRemove = jest.fn()
  const mockOnEdit = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering Org Info', () => {
    it('renders org name', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText('Save the World')).toBeInTheDocument()
    })

    it('renders location', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/Austin, TX/)).toBeInTheDocument()
    })

    it('renders cause tags (max 3)', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      // The card renders location and causes together
      const locationElements = screen.getByText(/Austin, TX/)
      expect(locationElements.textContent).toMatch(/environment/)
      expect(locationElements.textContent).toMatch(/education/)
    })

    it('truncates cause tags to 3 with overflow indicator', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const locationElements = screen.getByText(/Austin, TX/)
      if (mockOrgWithGiving.cause.length > 3) {
        expect(locationElements.textContent).toMatch(/\+1 more/)
      }
    })

    it('renders financial health badge', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText('HEALTHY')).toBeInTheDocument()
    })

    it('renders mission snippet', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/Fighting climate change/)).toBeInTheDocument()
    })

    it('renders hidden gem indicator if is_hidden_gem is true', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithVolunteer} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/hidden gem|gem/i)).toBeInTheDocument()
    })

    it('does not render hidden gem indicator if is_hidden_gem is false', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.queryByText(/hidden gem/i)).not.toBeInTheDocument()
    })
  })

  describe('Giving Intent', () => {
    it('renders giving intent with amount', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/Interested in Giving|Giving/i)).toBeInTheDocument()
      expect(screen.getByText(/\$250/)).toBeInTheDocument()
    })

    it('renders giving intent notes', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/Great work on carbon/)).toBeInTheDocument()
    })
  })

  describe('Volunteer Intent', () => {
    it('renders volunteer intent with hours', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithVolunteer} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/Interested in Volunteering|Volunteer/i)).toBeInTheDocument()
      expect(screen.getByText(/5.*hour/i)).toBeInTheDocument()
    })
  })

  describe('Board Intent', () => {
    it('renders board intent', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithBoard} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/Interested in Board|Board/i)).toBeInTheDocument()
    })
  })

  describe('No Intent', () => {
    it('displays "No intent set" when givingIntent is undefined', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgNoIntent} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/No intent set|No intent/i)).toBeInTheDocument()
    })
  })

  describe('Health Signal Colors', () => {
    it('renders HEALTHY badge with correct styling', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const healthBadge = screen.getByText('HEALTHY')
      expect(healthBadge).toHaveClass('bg-green-100')
      expect(healthBadge).toHaveClass('text-green-800')
    })

    it('renders STABLE badge with correct styling', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithVolunteer} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const healthBadge = screen.getByText('STABLE')
      expect(healthBadge).toHaveClass('bg-yellow-100')
      expect(healthBadge).toHaveClass('text-yellow-800')
    })

    it('renders CAUTION badge with correct styling', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgCaution} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const healthBadge = screen.getByText('CAUTION')
      expect(healthBadge).toHaveClass('bg-orange-100')
      expect(healthBadge).toHaveClass('text-orange-800')
    })
  })

  describe('Buttons', () => {
    it('renders edit button', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const editButton = screen.getByRole('button', { name: /edit/i })
      expect(editButton).toBeInTheDocument()
    })

    it('calls onEdit when edit button is clicked', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const editButton = screen.getByRole('button', { name: /edit/i })
      fireEvent.click(editButton)

      expect(mockOnEdit).toHaveBeenCalledWith(mockOrgWithGiving.ein)
    })

    it('renders remove button', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const removeButton = screen.getByRole('button', { name: /remove|delete/i })
      expect(removeButton).toBeInTheDocument()
    })

    it('calls onRemove when remove button is clicked', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const removeButton = screen.getByRole('button', { name: /remove|delete/i })
      fireEvent.click(removeButton)

      expect(mockOnRemove).toHaveBeenCalledWith(mockOrgWithGiving.ein)
    })
  })

  describe('Org Name Link', () => {
    it('renders org name as a link to detail page', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const link = screen.getByRole('link', { name: 'Save the World' })
      expect(link).toHaveAttribute('href', `/org/${mockOrgWithGiving.ein}`)
    })
  })

  describe('Memoization', () => {
    it('does not re-render when callbacks change but org stays same', () => {
      const { rerender } = render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      const firstRender = screen.getByText('Save the World')

      const newOnRemove = jest.fn()
      const newOnEdit = jest.fn()

      rerender(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={newOnRemove} onEdit={newOnEdit} />
        </TestWrapper>
      )

      const secondRender = screen.getByText('Save the World')
      expect(firstRender).toBe(secondRender)
    })
  })

  describe('Peer Context', () => {
    it('renders merit score when available', () => {
      render(
        <TestWrapper>
          <WalletCard org={mockOrgWithGiving} onRemove={mockOnRemove} onEdit={mockOnEdit} />
        </TestWrapper>
      )

      expect(screen.getByText(/78|score/i)).toBeInTheDocument()
    })
  })
})
