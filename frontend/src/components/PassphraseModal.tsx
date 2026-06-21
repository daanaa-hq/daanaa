import React, { useEffect, useState } from 'react'
import { generatePassphrase } from '../utils/wallet.crypto'

interface Props {
  mode: 'setup' | 'restore'
  onSetup: (passphrase: string) => Promise<void>
  onRestore: (passphrase: string) => Promise<void>
  onClose: () => void
}

export default function PassphraseModal({ mode, onSetup, onRestore, onClose }: Props) {
  const [passphrase, setPassphrase] = useState('')
  const [savedConfirmed, setSavedConfirmed] = useState(false)
  const [backupConfirmed, setBackupConfirmed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [restoreInput, setRestoreInput] = useState('')

  useEffect(() => {
    if (mode !== 'setup') return
    generatePassphrase()
      .then(setPassphrase)
      .catch(() => setError('Could not generate passphrase'))
  }, [mode])

  const canSetup = savedConfirmed && backupConfirmed && passphrase.length > 0

  async function handleSetup() {
    if (!canSetup) return
    setLoading(true)
    setError(null)
    try {
      await onSetup(passphrase)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Setup failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleRestore() {
    const phrase = restoreInput.trim()
    if (phrase.split(' ').length < 3) {
      setError('Enter your full passphrase')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await onRestore(phrase)
    } catch {
      setError('Passphrase not recognized. Check your words and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl">
        {mode === 'setup' ? (
          <>
            <h2 className="font-body text-xl font-semibold text-black font-semibold mb-2">
              Your wallet passphrase
            </h2>
            <p className="font-body text-sm text-black font-semibold mb-4">
              Write this down. It's the only way to access your wallet on another device.
              We cannot recover it.
            </p>
            {passphrase ? (
              <div className="bg-soft-cream rounded-xl p-4 mb-4 font-mono text-lg font-semibold text-black text-center tracking-wide select-all">
                {passphrase}
              </div>
            ) : (
              <div className="h-16 bg-soft-cream rounded-xl mb-4 animate-pulse" />
            )}
            <div className="space-y-3 mb-5">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={savedConfirmed}
                  onChange={e => setSavedConfirmed(e.target.checked)}
                  className="mt-0.5"
                />
                <span className="font-body text-sm text-black font-semibold">
                  I've saved my passphrase in a safe place
                </span>
              </label>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={backupConfirmed}
                  onChange={e => setBackupConfirmed(e.target.checked)}
                  className="mt-0.5"
                />
                <span className="font-body text-sm text-black font-semibold">
                  I'll download a backup after setup
                </span>
              </label>
            </div>
            {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 rounded-full font-body text-sm border border-light-grey text-black font-semibold hover:bg-soft-cream transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSetup}
                disabled={!canSetup || loading}
                aria-label="Set up wallet"
                className="flex-1 px-4 py-2 rounded-full font-body text-sm font-semibold bg-soft-gold text-black font-semibold hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? 'Setting up…' : 'Set up wallet'}
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 className="font-body text-xl font-semibold text-black font-semibold mb-2">
              Restore your wallet
            </h2>
            <p className="font-body text-sm text-black font-semibold mb-4">
              Enter your 4-word passphrase to access your wallet on this device.
            </p>
            <input
              type="text"
              value={restoreInput}
              onChange={e => setRestoreInput(e.target.value)}
              placeholder="e.g. correct horse battery staple"
              className="w-full border border-light-grey rounded-xl px-4 py-3 font-mono text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              autoComplete="off"
              spellCheck={false}
            />
            {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 rounded-full font-body text-sm border border-light-grey text-black font-semibold hover:bg-soft-cream transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRestore}
                disabled={loading}
                aria-label="Restore wallet"
                className="flex-1 px-4 py-2 rounded-full font-body text-sm font-semibold bg-soft-gold text-black font-semibold hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? 'Restoring…' : 'Restore wallet'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
