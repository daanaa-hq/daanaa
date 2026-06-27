import { useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useWallet } from '../contexts/WalletContext'
import { API_BASE } from '../lib/platform'

export default function WalletAutoSave() {
  const { user } = useAuth()
  const { entries } = useWallet()
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!user || entries.length === 0) return
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      user.getIdToken().then(token => {
        fetch(`${API_BASE}/api/wallet/backup`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ entries }),
        }).catch(() => {})
      })
    }, 3000)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [user?.uid, entries])

  return null
}
