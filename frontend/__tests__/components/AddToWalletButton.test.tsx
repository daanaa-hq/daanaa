import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { WalletContext } from '../../src/contexts/WalletContext'
import type { WalletContextType } from '../../src/types/wallet'

// Mock the API module BEFORE importing the component
jest.mock('../../src/data/api', () => ({
  getOrganization: jest.fn(),
}))

// Import after mock
import AddToWalletButton from '../../src/components/AddToWalletButton'
import * as api from '../../src/data/api'

describe('AddToWalletButton', () => {
  const mockApiOrg = {
    EIN: '111111111',
    organization_name: 'Save the World',
    CITY: 'Austin',
    STATE: 'TX',
    v5_context: {
      score: {
        percentile: 78,
        health_signal: 'HEALTHY' as const,
      },
    },
  }

  const mockWalletContextValue: WalletContextType = {
    wallet: {
      version: 1,
      lastUpdated: Date.now(),
      orgs: [],
      syncedWithServer: false,
    },
    addOrg: jest.fn(),
    removeOrg: jest.fn(),
    updateIntent: jest.fn(),
    isInWallet: jest.fn(() => false),
    getIntent: jest.fn(),
    syncToServer: jest.fn(),
    logoutAndClearSync: jest.fn(),
  }

  const renderWithContext = (
    component: React.ReactElement,
    contextValue = mockWalletContextValue
  ) => {
    return render(
      <BrowserRouter>
        <WalletContext.Provider value={contextValue}>
          {component}
        </WalletContext.Provider>
      </BrowserRouter>
    )
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders with org name', () => {
    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />
    )
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('shows "Add to Wallet" when org not in wallet', () => {
    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />
    )
    expect(screen.getByText(/add to wallet/i)).toBeInTheDocument()
  })

  it('shows "Already in Wallet" when org in wallet (disabled)', () => {
    const contextValue = {
      ...mockWalletContextValue,
      isInWallet: jest.fn(() => true),
    }
    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )
    const button = screen.getByRole('button')
    expect(button).toHaveTextContent(/already in wallet/i)
    expect(button).toBeDisabled()
  })

  it('fetches org from API on click', async () => {
    (api.getOrganization as jest.Mock).mockResolvedValueOnce(mockApiOrg)

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(api.getOrganization).toHaveBeenCalledWith(mockApiOrg.EIN)
    })
  })

  it('shows loading state while fetching', async () => {
    (api.getOrganization as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(mockApiOrg), 100)
        )
    )

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(screen.getByText(/adding/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.queryByText(/adding/i)).not.toBeInTheDocument()
    })
  })

  it('adds org to wallet on success', async () => {
    (api.getOrganization as jest.Mock).mockResolvedValueOnce(mockApiOrg)

    const addOrgMock = jest.fn()
    const contextValue = {
      ...mockWalletContextValue,
      addOrg: addOrgMock,
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(addOrgMock).toHaveBeenCalledWith(expect.objectContaining({ ein: mockApiOrg.EIN }))
    })
  })

  it('shows success state after add', async () => {
    (api.getOrganization as jest.Mock).mockResolvedValueOnce(mockApiOrg)

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/added to wallet/i)).toBeInTheDocument()
    })
  })

  it('resets to idle state after 3 seconds', async () => {
    (api.getOrganization as jest.Mock).mockResolvedValueOnce(mockApiOrg)

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Verify success state appears
    await waitFor(() => {
      expect(screen.getByText(/added to wallet/i)).toBeInTheDocument()
    })

    // After 3 seconds, should return to idle state
    await waitFor(
      () => {
        expect(screen.getByText(/add to wallet/i)).toBeInTheDocument()
      },
      { timeout: 4000 }
    )
  })

  it('shows error state on API failure', async () => {
    (api.getOrganization as jest.Mock).mockRejectedValueOnce(
      new Error('Not found')
    )

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/failed to add/i)).toBeInTheDocument()
    })
  })

  it('shows error state on network error', async () => {
    (api.getOrganization as jest.Mock).mockRejectedValueOnce(
      new Error('Network error')
    )

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/failed to add/i)).toBeInTheDocument()
    })
  })

  it('shows retry button in error state', async () => {
    (api.getOrganization as jest.Mock).mockRejectedValueOnce(
      new Error('Network error')
    )

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Error state should show error message and retry button
    await waitFor(() => {
      expect(screen.getByText(/failed to add/i)).toBeInTheDocument()
      expect(screen.getByText(/try again/i)).toBeInTheDocument()
    })
  })

  it('is keyboard accessible', async () => {
    (api.getOrganization as jest.Mock).mockResolvedValueOnce(mockApiOrg)

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')

    // Should be focusable
    button.focus()
    expect(button).toHaveFocus()

    // Click via keyboard equivalent (using click on focused button)
    fireEvent.click(button)

    await waitFor(() => {
      expect(contextValue.addOrg).toHaveBeenCalled()
    })
  })

  it('has proper aria-label', () => {
    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />
    )
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label')
  })

  it('calls onAdded callback if provided', async () => {
    (api.getOrganization as jest.Mock).mockResolvedValueOnce(mockApiOrg)

    const onAddedMock = jest.fn()
    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton
        ein={mockApiOrg.EIN}
        orgName={mockApiOrg.organization_name}
        onAdded={onAddedMock}
      />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(onAddedMock).toHaveBeenCalledWith(mockApiOrg.EIN)
    })
  })

  it('button has type="button" (not submit)', () => {
    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />
    )
    expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
  })

  it('disabled state when loading', async () => {
    (api.getOrganization as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(mockApiOrg), 200)
        )
    )

    const contextValue = {
      ...mockWalletContextValue,
      addOrg: jest.fn(),
    }

    renderWithContext(
      <AddToWalletButton ein={mockApiOrg.EIN} orgName={mockApiOrg.organization_name} />,
      contextValue
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(button).toBeDisabled()
    })
  })
})
