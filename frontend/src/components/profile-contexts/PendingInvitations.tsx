import { useEffect, useState } from 'react'
import { Clock, Check, X } from 'lucide-react'
import type { PendingInvitation } from '../../hooks/useProfileContexts'

const CONTEXT_LABELS: Record<string, string> = {
  household: '👨‍👩‍👧‍👦 Household',
  daf: '💰 DAF or Foundation',
  business: '🏢 Business',
  other: '📋 Other',
}

interface PendingInvitationsProps {
  getPendingInvitations: () => Promise<PendingInvitation[]>
  acceptInvitation: (invitationId: string) => Promise<void>
  rejectInvitation: (invitationId: string) => Promise<void>
  onActionComplete: () => void
}

export default function PendingInvitations({
  getPendingInvitations,
  acceptInvitation,
  rejectInvitation,
  onActionComplete,
}: PendingInvitationsProps) {
  const [invitations, setInvitations] = useState<PendingInvitation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionInProgress, setActionInProgress] = useState<string | null>(null)

  const fetchInvitations = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getPendingInvitations()
      setInvitations(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load invitations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInvitations()
  }, [])

  const handleAccept = async (invitationId: string) => {
    setActionInProgress(invitationId)
    try {
      await acceptInvitation(invitationId)
      setInvitations(prev => prev.filter(inv => inv.invitation_id !== invitationId))
      onActionComplete()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept invitation')
    } finally {
      setActionInProgress(null)
    }
  }

  const handleReject = async (invitationId: string) => {
    setActionInProgress(invitationId)
    try {
      await rejectInvitation(invitationId)
      setInvitations(prev => prev.filter(inv => inv.invitation_id !== invitationId))
      onActionComplete()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject invitation')
    } finally {
      setActionInProgress(null)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-dark-brown mb-4">Pending Invitations</h2>
        <div className="text-center py-4">
          <div className="w-4 h-4 rounded-full border-2 border-soft-gold border-t-transparent animate-spin mx-auto" />
        </div>
      </div>
    )
  }

  if (invitations.length === 0) {
    return null
  }

  return (
    <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="text-blue-600" size={20} />
        <h2 className="text-lg font-semibold text-dark-brown">Pending Invitations ({invitations.length})</h2>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {invitations.map((invitation) => {
          const expiresAt = new Date(invitation.expires_at)
          const isExpiring = expiresAt.getTime() - Date.now() < 24 * 60 * 60 * 1000
          const daysLeft = Math.ceil((expiresAt.getTime() - Date.now()) / (24 * 60 * 60 * 1000))

          return (
            <div key={invitation.invitation_id} className="bg-white rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="font-semibold text-dark-brown">
                    {CONTEXT_LABELS[invitation.context_type]}
                  </div>
                  <div className="text-sm text-dark-gray">
                    {invitation.role === 'lead' ? '👑 ' : ''}
                    {invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)} role
                  </div>
                  <div className={`text-xs mt-1 ${isExpiring ? 'text-red-600' : 'text-gray-500'}`}>
                    Expires in {daysLeft} {daysLeft === 1 ? 'day' : 'days'}
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleAccept(invitation.invitation_id)}
                  disabled={actionInProgress === invitation.invitation_id}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-100 hover:bg-green-200 disabled:bg-gray-200 text-green-700 rounded-lg transition font-medium text-sm"
                >
                  <Check size={16} />
                  Accept
                </button>
                <button
                  onClick={() => handleReject(invitation.invitation_id)}
                  disabled={actionInProgress === invitation.invitation_id}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-100 hover:bg-red-200 disabled:bg-gray-200 text-red-700 rounded-lg transition font-medium text-sm"
                >
                  <X size={16} />
                  Reject
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
