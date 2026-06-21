import React from 'react'
import { useWallet } from '../contexts/WalletContext'
import IntentModal from './IntentModal'
import type { GivingIntent, WalletEntry } from '../types/wallet'

interface EditIntentModalProps {
  ein: string
  orgName: string
  givingIntent?: GivingIntent
  isOpen: boolean
  onClose: () => void
}

export default function EditIntentModal({
  ein,
  orgName,
  givingIntent,
  isOpen,
  onClose,
}: EditIntentModalProps) {
  const { updateIntent } = useWallet()

  const handleSave = (entryEin: string, intent: GivingIntent) => {
    try {
      updateIntent(entryEin, intent)
    } catch (err) {
      console.error('Failed to update intent:', err)
    }
  }

  return (
    <IntentModal
      ein={ein}
      orgName={orgName}
      isOpen={isOpen}
      onClose={onClose}
      onSave={handleSave}
      initialIntent={givingIntent}
    />
  )
}
