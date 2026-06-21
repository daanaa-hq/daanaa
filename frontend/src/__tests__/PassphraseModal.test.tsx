import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PassphraseModal from '../components/PassphraseModal'

jest.mock('../utils/wallet.crypto', () => ({
  generatePassphrase: jest.fn().mockResolvedValue('correct horse battery staple'),
}))

describe('PassphraseModal — setup mode', () => {
  it('shows 4 generated words', async () => {
    render(<PassphraseModal mode="setup" onSetup={jest.fn()} onRestore={jest.fn()} onClose={jest.fn()} />)
    await waitFor(() => {
      expect(screen.getByText(/correct horse battery staple/i)).toBeInTheDocument()
    })
  })

  it('setup button disabled until both checkboxes checked', async () => {
    render(<PassphraseModal mode="setup" onSetup={jest.fn()} onRestore={jest.fn()} onClose={jest.fn()} />)
    await waitFor(() => screen.getByText(/correct horse battery staple/i))
    const btn = screen.getByRole('button', { name: /set up wallet/i })
    expect(btn).toBeDisabled()
  })

  it('calls onSetup with passphrase when both confirmed', async () => {
    const onSetup = jest.fn()
    render(<PassphraseModal mode="setup" onSetup={onSetup} onRestore={jest.fn()} onClose={jest.fn()} />)
    await waitFor(() => screen.getByText(/correct horse battery staple/i))
    // Check both boxes
    const checkboxes = screen.getAllByRole('checkbox')
    checkboxes.forEach(cb => fireEvent.click(cb))
    fireEvent.click(screen.getByRole('button', { name: /set up wallet/i }))
    await waitFor(() => expect(onSetup).toHaveBeenCalledWith('correct horse battery staple'))
  })
})

describe('PassphraseModal — restore mode', () => {
  it('shows restore UI (not setup UI)', () => {
    render(<PassphraseModal mode="restore" onSetup={jest.fn()} onRestore={jest.fn()} onClose={jest.fn()} />)
    expect(screen.getByRole('button', { name: /restore/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /set up wallet/i })).not.toBeInTheDocument()
  })

  it('calls onRestore with entered passphrase', async () => {
    const onRestore = jest.fn().mockResolvedValue(undefined)
    render(<PassphraseModal mode="restore" onSetup={jest.fn()} onRestore={onRestore} onClose={jest.fn()} />)
    const input = screen.getByRole('textbox')
    const user = userEvent.setup()
    await user.type(input, 'my four word phrase')
    fireEvent.click(screen.getByRole('button', { name: /restore/i }))
    await waitFor(() => expect(onRestore).toHaveBeenCalledWith('my four word phrase'))
  })
})
