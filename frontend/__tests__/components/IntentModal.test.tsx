import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import IntentModal from '../../src/components/IntentModal'
import type { WalletOrg, GivingIntent } from '../../src/types/wallet'

describe('IntentModal', () => {
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
  }

  const mockOnSave = jest.fn()
  const mockOnClose = jest.fn()

  beforeEach(() => {
    mockOnSave.mockClear()
    mockOnClose.mockClear()
  })

  describe('rendering', () => {
    it('should render modal when isOpen is true', () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      expect(screen.getByText(/Add Giving Intent/i)).toBeInTheDocument()
    })

    it('should not render modal when isOpen is false', () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={false}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      expect(screen.queryByText(/Add Giving Intent/i)).not.toBeInTheDocument()
    })

    it('should display org name in modal title', () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      expect(screen.getByText(new RegExp(mockOrg.name))).toBeInTheDocument()
    })

    it('should show three intent type options', () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      expect(screen.getByLabelText(/Give Money/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Volunteer/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Join Board/i)).toBeInTheDocument()
    })
  })

  describe('type selection', () => {
    it('should show amount input when "giving" type is selected', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)
      expect(screen.getByLabelText(/Amount/i)).toBeInTheDocument()
    })

    it('should show hours input when "volunteer" type is selected', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const volunteerRadio = screen.getByLabelText(/Volunteer/i)
      await userEvent.click(volunteerRadio)
      expect(screen.getByLabelText(/Hours/i)).toBeInTheDocument()
    })

    it('should show minimal form for "board" type', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const boardRadio = screen.getByLabelText(/Join Board/i)
      await userEvent.click(boardRadio)
      // Board interest should not require amount or hours
      expect(screen.queryByLabelText(/Amount/i)).not.toBeInTheDocument()
      expect(screen.queryByLabelText(/Hours/i)).not.toBeInTheDocument()
    })
  })

  describe('amount validation', () => {
    it('should accept valid amounts (1-999999)', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)

      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.type(amountInput, '500')
      expect(amountInput.value).toBe('500')
    })

    it('should reject amounts less than 1', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)

      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.type(amountInput, '0')
      // Validation should trigger on save
      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)
      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/Amount must be/i)).toBeInTheDocument()
      })
    })

    it('should reject amounts greater than 999999', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)

      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      await userEvent.type(amountInput, '1000000')
      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)
      await waitFor(() => {
        expect(screen.getByText(/Amount must be/i)).toBeInTheDocument()
      })
    })
  })

  describe('hours validation', () => {
    it('should accept valid hours (0-168)', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const volunteerRadio = screen.getByLabelText(/Volunteer/i)
      await userEvent.click(volunteerRadio)

      const hoursInput = screen.getByLabelText(/Hours/i) as HTMLInputElement
      await userEvent.type(hoursInput, '10')
      expect(hoursInput.value).toBe('10')
    })

    it('should reject hours greater than 168', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const volunteerRadio = screen.getByLabelText(/Volunteer/i)
      await userEvent.click(volunteerRadio)

      const hoursInput = screen.getByLabelText(/Hours/i) as HTMLInputElement
      await userEvent.type(hoursInput, '200')
      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)
      await waitFor(() => {
        expect(screen.getByText(/Hours must be/i)).toBeInTheDocument()
      })
    })
  })

  describe('notes validation', () => {
    it('should accept notes up to 200 characters', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const notesInput = screen.getByLabelText(/Notes/i) as HTMLTextAreaElement
      const testNotes = 'A'.repeat(200)
      await userEvent.type(notesInput, testNotes)
      expect(notesInput.value).toBe(testNotes)
    })

    it('should enforce 200 character max length on input', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const notesInput = screen.getByLabelText(/Notes/i) as HTMLTextAreaElement
      // maxLength attribute prevents entering more than 200 chars
      expect(notesInput.maxLength).toBe(200)
      const testNotes = 'A'.repeat(201)
      await userEvent.type(notesInput, testNotes)
      // Input should be capped at 200
      expect(notesInput.value.length).toBeLessThanOrEqual(200)
    })

    it('should display character counter', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const notesInput = screen.getByLabelText(/Notes/i)
      await userEvent.type(notesInput, 'Test note')
      expect(screen.getByText(/9 \/ 200/i)).toBeInTheDocument()
    })
  })

  describe('pre-filling with initialIntent', () => {
    it('should pre-fill form when initialIntent is provided', () => {
      const initialIntent: GivingIntent = {
        type: 'giving',
        status: 'interested',
        amount: 500,
        addedAt: Date.now(),
        notes: 'Support their work',
      }
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          initialIntent={initialIntent}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i) as HTMLInputElement
      const amountInput = screen.getByLabelText(/Amount/i) as HTMLInputElement
      const notesInput = screen.getByLabelText(/Notes/i) as HTMLTextAreaElement

      expect(givingRadio.checked).toBe(true)
      expect(amountInput.value).toBe('500')
      expect(notesInput.value).toBe('Support their work')
    })

    it('should pre-fill volunteer hours from initialIntent', () => {
      const initialIntent: GivingIntent = {
        type: 'volunteer',
        status: 'interested',
        hours: 5,
        addedAt: Date.now(),
      }
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
          initialIntent={initialIntent}
        />
      )
      const volunteerRadio = screen.getByLabelText(/Volunteer/i) as HTMLInputElement
      const hoursInput = screen.getByLabelText(/Hours/i) as HTMLInputElement

      expect(volunteerRadio.checked).toBe(true)
      expect(hoursInput.value).toBe('5')
    })
  })

  describe('save handler', () => {
    it('should call onSave with correct intent when form is valid', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)

      const amountInput = screen.getByLabelText(/Amount/i)
      await userEvent.type(amountInput, '250')

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(mockOrg.ein, expect.objectContaining({
          type: 'giving',
          status: 'interested',
          amount: 250,
        }))
      })
    })

    it('should not call onSave if validation fails', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)

      const amountInput = screen.getByLabelText(/Amount/i)
      await userEvent.type(amountInput, '0')

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockOnSave).not.toHaveBeenCalled()
      })
    })

    it('should include addedAt timestamp in intent', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const volunteerRadio = screen.getByLabelText(/Volunteer/i)
      await userEvent.click(volunteerRadio)

      const hoursInput = screen.getByLabelText(/Hours/i)
      await userEvent.type(hoursInput, '3')

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          mockOrg.ein,
          expect.objectContaining({
            addedAt: expect.any(Number),
          })
        )
      })
    })
  })

  describe('cancel handler', () => {
    it('should call onClose when cancel button is clicked', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)
      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should not call onSave when cancel is clicked', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const cancelButton = screen.getByText('Cancel')
      await userEvent.click(cancelButton)
      expect(mockOnSave).not.toHaveBeenCalled()
    })

    it('should call onClose when Escape key is pressed', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('keyboard navigation', () => {
    it('should allow Tab navigation through form fields', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.tab()
      expect(givingRadio).toHaveFocus()
    })

    it('should close modal on Escape key', async () => {
      const { container } = render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const modal = container.querySelector('[role="dialog"]')
      expect(modal).toBeInTheDocument()
      fireEvent.keyDown(modal!, { key: 'Escape', code: 'Escape' })
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('frequency selection (for giving)', () => {
    it('should show frequency options when giving type is selected', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)
      expect(screen.getByLabelText(/Per Year/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Per Month/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/One-time/i)).toBeInTheDocument()
    })

    it('should include frequency in saved intent', async () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const givingRadio = screen.getByLabelText(/Give Money/i)
      await userEvent.click(givingRadio)

      const amountInput = screen.getByLabelText(/Amount/i)
      await userEvent.type(amountInput, '100')

      const monthlyRadio = screen.getByLabelText(/Per Month/i)
      await userEvent.click(monthlyRadio)

      const saveButton = screen.getByText('Save')
      await userEvent.click(saveButton)

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(
          mockOrg.ein,
          expect.objectContaining({
            amount: 100,
            frequency: 'month',
          })
        )
      })
    })
  })

  describe('accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      expect(screen.getByLabelText(/Give Money/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Volunteer/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Join Board/i)).toBeInTheDocument()
    })

    it('should have a close button with aria-label', () => {
      render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const closeButton = screen.getByLabelText(/Close/i)
      expect(closeButton).toBeInTheDocument()
    })

    it('should render as a dialog with proper role', () => {
      const { container } = render(
        <IntentModal
          org={mockOrg}
          isOpen={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      )
      const modal = container.querySelector('[role="dialog"]')
      expect(modal).toBeInTheDocument()
    })
  })
})
