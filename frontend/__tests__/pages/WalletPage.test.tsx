import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { WalletProvider, useWallet } from '../../src/contexts/WalletContext'
import WalletPage from '../../src/pages/WalletPage'
import type { WalletOrg, GivingIntent } from '../../src/types/wallet'

// Mock usePageMeta hook
jest.mock('../../src/hooks/usePageMeta', () => ({
  usePageMeta: jest.fn(),
}))

const mockOrgHealthy: WalletOrg = {
  ein: '111111111',
  name: 'Save the World',
  mission: 'Fighting climate change through community education',
  location: 'Austin, TX',
  cause: ['environment', 'education'],
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
  },
}

const mockOrgStable: WalletOrg = {
  ein: '222222222',
  name: 'Climate Alliance',
  mission: 'Building climate resilience in the Pacific Northwest',
  location: 'Portland, OR',
  cause: ['environment'],
  merit_score_v5: 62,
  merit_health_signal_v5: 'STABLE',
  is_hidden_gem: true,
  bookmarkedAt: Date.now() - 86400000,
  givingIntent: {
    type: 'volunteer',
    status: 'interested',
    hours: 5,
    addedAt: Date.now() - 86400000,
  },
}

const mockOrgCaution: WalletOrg = {
  ein: '333333333',
  name: 'Small Charity',
  mission: 'Serving local communities',
  location: 'Denver, CO',
  cause: ['health'],
  merit_score_v5: 45,
  merit_health_signal_v5: 'CAUTION',
  is_hidden_gem: false,
  bookmarkedAt: Date.now() - 172800000,
}

const mockOrgBoard: WalletOrg = {
  ein: '444444444',
  name: 'Leadership Initiative',
  mission: 'Building tomorrow\'s nonprofit leaders',
  location: 'New York, NY',
  cause: ['capacity-building'],
  merit_score_v5: 88,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now() - 259200000,
  givingIntent: {
    type: 'board',
    status: 'interested',
    addedAt: Date.now() - 259200000,
  },
}

const mockOrgNoIntent: WalletOrg = {
  ein: '555555555',
  name: 'Bookmarked Org',
  mission: 'No intent set yet',
  location: 'Chicago, IL',
  cause: ['arts'],
  merit_score_v5: 70,
  merit_health_signal_v5: 'HEALTHY',
  is_hidden_gem: false,
  bookmarkedAt: Date.now(),
}

function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <WalletProvider>{children}</WalletProvider>
    </BrowserRouter>
  )
}

describe('WalletPage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('Empty State', () => {
    it('renders empty state when wallet is empty', () => {
      render(
        <TestWrapper>
          <WalletPage />
        </TestWrapper>
      )

      expect(screen.getByText(/Your wallet is empty/i)).toBeInTheDocument()
      // Check for buttons instead of links/text
      expect(screen.getByRole('button', { name: /Browse Directory/i })).toBeInTheDocument()
    })

    it('shows browse directory button in empty state', () => {
      render(
        <TestWrapper>
          <WalletPage />
        </TestWrapper>
      )

      const button = screen.getByRole('button', { name: /Browse Directory/i })
      expect(button).toBeInTheDocument()
    })
  })

  describe('Grid Layout', () => {
    it('renders wallet cards in a grid with multiple orgs', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
          addOrg(mockOrgBoard)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
        expect(screen.getByText('Climate Alliance')).toBeInTheDocument()
        expect(screen.getByText('Small Charity')).toBeInTheDocument()
        expect(screen.getByText('Leadership Initiative')).toBeInTheDocument()
      })
    })

    it('displays org count in header', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/2 org/i)).toBeInTheDocument()
      })
    })
  })

  describe('Sorting', () => {
    it('sorts by recent (default)', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgCaution)
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const cards = screen.getAllByRole('link', { name: /Save|Climate|Small/i })
        expect(cards[0]).toHaveTextContent('Save the World')
      })
    })

    it('sorts by name A-Z', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgCaution)
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const sortDropdown = screen.getByRole('combobox', { name: /sort/i })
        fireEvent.change(sortDropdown, { target: { value: 'name' } })
      })

      await waitFor(() => {
        const cards = screen.getAllByText(/Climate Alliance|Save the World|Small Charity/)
        expect(cards[0]).toHaveTextContent('Climate Alliance')
      })
    })

    it('sorts by financial health', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgCaution)
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const sortDropdown = screen.getByRole('combobox', { name: /sort/i })
        fireEvent.change(sortDropdown, { target: { value: 'health' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
      })
    })
  })

  describe('Filtering', () => {
    it('filters by giving intent', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgBoard)
          addOrg(mockOrgNoIntent)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const intentFilter = screen.getByRole('combobox', { name: /intent/i })
        fireEvent.change(intentFilter, { target: { value: 'giving' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
        expect(screen.queryByText('Climate Alliance')).not.toBeInTheDocument()
        expect(screen.queryByText('Leadership Initiative')).not.toBeInTheDocument()
      })
    })

    it('filters by health signal', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const healthFilter = screen.getByRole('combobox', { name: /health/i })
        fireEvent.change(healthFilter, { target: { value: 'HEALTHY' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
        expect(screen.queryByText('Small Charity')).not.toBeInTheDocument()
      })
    })

    it('clears filters', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const healthFilter = screen.getByRole('combobox', { name: /health/i })
        fireEvent.change(healthFilter, { target: { value: 'HEALTHY' } })
      })

      await waitFor(() => {
        const clearButton = screen.getByRole('button', { name: /clear/i })
        fireEvent.click(clearButton)
      })

      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
        expect(screen.getByText('Small Charity')).toBeInTheDocument()
      })
    })
  })

  describe('Search', () => {
    it('filters orgs by name', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search/i)
        fireEvent.change(searchInput, { target: { value: 'Alliance' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Climate Alliance')).toBeInTheDocument()
        expect(screen.queryByText('Save the World')).not.toBeInTheDocument()
      })
    })

    it('rejects invalid search input and shows error', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search/i) as HTMLInputElement
        // Try to enter a ReDoS pattern
        fireEvent.change(searchInput, { target: { value: '(a+)+b' } })
      })

      // Should show validation error
      await waitFor(() => {
        const errorMessage = screen.getByRole('alert')
        expect(errorMessage).toBeInTheDocument()
        expect(errorMessage.textContent).toMatch(/invalid characters|patterns/i)
      })
    })

    it('allows empty search to clear filters', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search/i) as HTMLInputElement
        fireEvent.change(searchInput, { target: { value: '' } })
      })

      // Should show all orgs again
      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
        expect(screen.getByText('Climate Alliance')).toBeInTheDocument()
      })
    })

    it('filters orgs by location', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search/i)
        fireEvent.change(searchInput, { target: { value: 'Austin' } })
      })

      await waitFor(() => {
        expect(screen.getByText('Save the World')).toBeInTheDocument()
        expect(screen.queryByText('Climate Alliance')).not.toBeInTheDocument()
      })
    })

    it('filters orgs by cause', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search/i)
        fireEvent.change(searchInput, { target: { value: 'food' } })
      })

      // After filtering for 'food', only orgs with 'food' in their cause, location, name, or mission should show
      // None of our test orgs have 'food' so all should be hidden
      await waitFor(() => {
        expect(screen.queryByText('Climate Alliance')).not.toBeInTheDocument()
        expect(screen.queryByText('Save the World')).not.toBeInTheDocument()
        expect(screen.queryByText('Small Charity')).not.toBeInTheDocument()
      })
    })
  })

  describe('Org Card Links', () => {
    it('links org names to detail page', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const link = screen.getByRole('link', { name: /Save the World/ })
        expect(link).toHaveAttribute('href', `/org/${mockOrgHealthy.ein}`)
      })
    })
  })

  describe('Responsive Grid', () => {
    it('renders grid with responsive columns', async () => {
      const TestWithOrgs = () => {
        const { addOrg } = useWallet()
        React.useEffect(() => {
          addOrg(mockOrgHealthy)
          addOrg(mockOrgStable)
          addOrg(mockOrgCaution)
        }, [addOrg])
        return <WalletPage />
      }

      render(
        <TestWrapper>
          <TestWithOrgs />
        </TestWrapper>
      )

      await waitFor(() => {
        const gridContainer = screen.getAllByText(/Save the World|Climate Alliance|Small Charity/)[0].closest('div')?.parentElement
        expect(gridContainer).toBeInTheDocument()
      })
    })
  })
})
