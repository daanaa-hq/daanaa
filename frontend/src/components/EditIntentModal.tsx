import React from 'react'
import { useWallet } from '../contexts/WalletContext'
import IntentModal from './IntentModal'
import type { WalletOrg, GivingIntent } from '../types/wallet'

interface EditIntentModalProps {
  org: WalletOrg
  isOpen: boolean
  onClose: () => void
}

/**
 * EditIntentModal: Wrapper around IntentModal with WalletContext integration
 * Automatically handles saving to wallet context and error handling
 * Can be used to edit an existing intent or add a new one
 */
export default function EditIntentModal({
  org,
  isOpen,
  onClose,
}: EditIntentModalProps) {
  const { updateIntent } = useWallet()

  const handleSave = (ein: string, intent: GivingIntent) => {
    try {
      updateIntent(ein, intent)
      // Modal closes automatically via onClose
    } catch (err) {
      // Error is logged in updateIntent via validation
      console.error('Failed to update intent:', err)
    }
  }

  return (
    <IntentModal
      org={org}
      isOpen={isOpen}
      onClose={onClose}
      onSave={handleSave}
      initialIntent={org.givingIntent}
    />
  )
}
