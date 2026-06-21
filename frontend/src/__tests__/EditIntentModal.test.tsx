import React from 'react'
import { render, screen } from '@testing-library/react'
import EditIntentModal from '../components/EditIntentModal'
import type { GivingIntent } from '../types/wallet'

jest.mock('../contexts/WalletContext', () => ({
  useWallet: () => ({ updateIntent: jest.fn() }),
}))

const onClose = jest.fn()
const defaultProps = {
  ein: '123456789',
  orgName: 'Ocean Conservancy',
  isOpen: true,
  onClose,
}

describe('EditIntentModal', () => {
  it('renders edit mode when givingIntent provided', () => {
    const givingIntent: GivingIntent = { type: 'giving', addedAt: Date.now(), amount: 50 }
    render(<EditIntentModal {...defaultProps} givingIntent={givingIntent} />)
    expect(screen.getByText(/edit your intent for ocean conservancy/i)).toBeInTheDocument()
  })

  it('renders new intent flow when no givingIntent', () => {
    render(<EditIntentModal {...defaultProps} />)
    expect(screen.getByText(/how would you like to support ocean conservancy/i)).toBeInTheDocument()
  })

  it('does not render when isOpen is false', () => {
    render(<EditIntentModal {...defaultProps} isOpen={false} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
