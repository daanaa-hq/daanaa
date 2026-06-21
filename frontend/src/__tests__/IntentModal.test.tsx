import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import IntentModal from '../components/IntentModal'
import type { GivingIntent } from '../types/wallet'

const onSave = jest.fn()
const onClose = jest.fn()
const defaultProps = {
  ein: '123456789',
  orgName: 'Save the World',
  isOpen: true,
  onClose,
  onSave,
}

beforeEach(() => {
  onSave.mockClear()
  onClose.mockClear()
})

describe('IntentModal', () => {
  it('renders type selection step when no initialIntent', () => {
    render(<IntentModal {...defaultProps} />)
    expect(screen.getByText(/how would you like to support save the world/i)).toBeInTheDocument()
    expect(screen.getByText('Give money')).toBeInTheDocument()
    expect(screen.getByText('Volunteer')).toBeInTheDocument()
  })

  it('proceeds to details step on type click', () => {
    render(<IntentModal {...defaultProps} />)
    fireEvent.click(screen.getByText('Give money'))
    expect(screen.getByLabelText(/amount/i)).toBeInTheDocument()
  })

  it('renders edit flow when initialIntent provided', () => {
    const initialIntent: GivingIntent = { type: 'giving', addedAt: Date.now(), amount: 100, frequency: 'year' }
    render(<IntentModal {...defaultProps} initialIntent={initialIntent} />)
    expect(screen.getByText(/edit your intent for save the world/i)).toBeInTheDocument()
  })

  it('calls onClose when Escape pressed', () => {
    render(<IntentModal {...defaultProps} />)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('does not render when isOpen is false', () => {
    render(<IntentModal {...defaultProps} isOpen={false} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
