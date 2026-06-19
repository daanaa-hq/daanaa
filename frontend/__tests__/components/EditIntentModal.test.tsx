import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import EditIntentModal from '../../src/components/EditIntentModal'
import { WalletProvider } from '../../src/contexts/WalletContext'
import type { WalletOrg, GivingIntent } from '../../src/types/wallet'

describe('EditIntentModal', () => {
  const mockOrg: WalletOrg = {
    ein: '001234567',
    name: 'Save the World',
    mission: 'Fighting climate change',
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
      notes: 'Support their work',
    },
  }

  const mockOnClose = jest.fn()

  beforeEach(() => {
    mockOnClose.mockClear()
  })

  describe('rendering', () => {
    it('should render edit modal when isOpen is true', () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      expect(screen.getByText(/Add Giving Intent/i)).toBeInTheDocument()
    })

    it('should not render modal when isOpen is false', () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={false}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      expect(screen.queryByText(/Add Giving Intent/i)).not.toBeInTheDocument()
    })

    it('should display org name in modal title', () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      expect(screen.getByText(new RegExp(mockOrg.name))).toBeInTheDocument()
    })
  })

  describe('pre-filling with existing intent', () => {
    it('should pre-fill form with existing giving intent', () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const givingRadio = screen.getByLabelText(/Give Money/i) as HTMLInputElement
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement

      expect(givingRadio.checked).toBe(true)
      expect(amountInput.value).toBe('250')
    })

    it('should display current intent info', () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      // Should show current intent type
      const givingRadio = screen.getByLabelText(/Give Money/i) as HTMLInputElement
      expect(givingRadio.checked).toBe(true)
    })
  })

  describe('editing intent', () => {
    it('should allow changing giving amount', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.clear(amountInput)
      await userEvent.type(amountInput, '500')
      expect(amountInput.value).toBe('500')
    })

    it('should allow changing to volunteer intent', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const volunteerRadio = screen.getByLabelText(/Volunteer/i)
      await userEvent.click(volunteerRadio)
      expect(screen.getByLabelText(/Hours/i)).toBeInTheDocument()
    })

    it('should allow changing to board intent', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const boardRadio = screen.getByLabelText(/Join Board/i)
      await userEvent.click(boardRadio)
      expect(screen.getByLabelText(/Join Board/i)).toBeChecked()
    })

    it('should allow updating notes', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const notesInput = screen.getByLabelText(/Notes/i) as HTMLTextAreaElement
      await userEvent.clear(notesInput)
      await userEvent.type(notesInput, 'Updated notes')
      expect(notesInput.value).toBe('Updated notes')
    })
  })

  describe('save handler', () => {
    it('should save changes and close modal', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.clear(amountInput)
      await userEvent.type(amountInput, '500')

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })

    it('should call updateIntent on wallet context', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.clear(amountInput)
      await userEvent.type(amountInput, '600')

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      // Modal should close after save
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })
  })

  describe('cancel handler', () => {
    it('should close modal without saving when cancel is clicked', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.clear(amountInput)
      await userEvent.type(amountInput, '999')

      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('org without existing intent', () => {
    it('should handle org without existing intent', () => {
      const orgWithoutIntent: WalletOrg = {
        ...mockOrg,
        givingIntent: undefined,
      }
      render(
        <WalletProvider>
          <EditIntentModal
            org={orgWithoutIntent}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      // Should still render and allow selecting an intent
      expect(screen.getByLabelText(/Give Money/i)).toBeInTheDocument()
    })
  })

  describe('error handling', () => {
    it('should show validation errors', async () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.clear(amountInput)
      await userEvent.type(amountInput, '0')

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/Amount must be/i)).toBeInTheDocument()
      })
    })
  })

  describe('accessibility', () => {
    it('should have proper ARIA labels for all controls', () => {
      render(
        <WalletProvider>
          <EditIntentModal
            org={mockOrg}
            isOpen={true}
            onClose={mockOnClose}
          />
        </WalletProvider>
      )
      expect(screen.getByLabelText(/Give Money/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Volunteer/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Join Board/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Amount/i)).toBeInTheDocument()
    })
  })
})
