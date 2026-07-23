import { useState, useEffect } from 'react'
import { X, UserPlus, Shield, Trash2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import type { ProfileContext, ContextMember } from '../../hooks/useProfileContexts'

const ROLE_LABELS: Record<string, string> = {
  lead: '👑 Lead',
  support: '🤝 Support',
  member: '👤 Member',
  viewer: '👁️ Viewer',
}

const ROLE_DESCRIPTIONS: Record<string, string> = {
  lead: 'Full control: invite, remove, change roles, archive',
  support: 'Can invite and remove members',
  member: 'Read-only access',
  viewer: 'View-only access',
}

const AVAILABLE_ROLES = ['lead', 'support', 'member', 'viewer']

interface MemberManagementProps {
  contextId: string
  context: ProfileContext
  onClose: () => void
  getMembers: (contextId: string) => Promise<ContextMember[]>
  inviteMember: (contextId: string, uid: string, role: string) => Promise<string>
  updateMemberRole: (contextId: string, uid: string, role: string) => Promise<void>
  removeMember: (contextId: string, uid: string) => Promise<void>
  onMembersUpdated: () => void
}

export default function MemberManagement({
  contextId,
  context,
  onClose,
  getMembers,
  inviteMember,
  updateMemberRole,
  removeMember,
  onMembersUpdated,
}: MemberManagementProps) {
  const { user } = useAuth()
  const [members, setMembers] = useState<ContextMember[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteUid, setInviteUid] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [inviting, setInviting] = useState(false)

  const canInvite = context.role === 'lead' || context.role === 'support'
  const isLead = context.role === 'lead'

  useEffect(() => {
    const fetchMembers = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getMembers(contextId)
        setMembers(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load members')
      } finally {
        setLoading(false)
      }
    }
    fetchMembers()
  }, [contextId, getMembers])

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inviteUid.trim()) {
      setError('Firebase UID is required')
      return
    }

    setInviting(true)
    setError(null)
    try {
      await inviteMember(contextId, inviteUid.trim(), inviteRole)
      setInviteUid('')
      setInviteRole('member')
      setShowInviteForm(false)
      onMembersUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invite member')
    } finally {
      setInviting(false)
    }
  }

  const handleUpdateRole = async (uid: string, newRole: string) => {
    if (uid === user?.uid && newRole !== 'lead') {
      setError('You cannot demote yourself')
      return
    }

    setError(null)
    try {
      await updateMemberRole(contextId, uid, newRole)
      setMembers(prev => prev.map(m => m.firebase_uid === uid ? { ...m, role: newRole as any } : m))
      onMembersUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update role')
    }
  }

  const handleRemove = async (uid: string) => {
    if (uid === user?.uid) {
      setError('You cannot remove yourself')
      return
    }

    if (!confirm('Remove this member from the context?')) return

    setError(null)
    try {
      await removeMember(contextId, uid)
      setMembers(prev => prev.filter(m => m.firebase_uid !== uid))
      onMembersUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member')
    }
  }

  // Mask UID display based on role
  const maskUid = (uid: string) => {
    if (isLead) return uid
    if (uid === user?.uid) return uid
    const lastSix = uid.slice(-6)
    return `user_${lastSix}`
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 p-6 sticky top-0 bg-white">
          <h2 className="text-xl font-bold text-dark-brown">Manage Members</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Invite Form */}
          {canInvite && (
            <div className="mb-8">
              {!showInviteForm ? (
                <button
                  onClick={() => setShowInviteForm(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-soft-gold text-soft-gold hover:bg-amber-50 rounded-lg transition font-medium"
                >
                  <UserPlus size={18} />
                  Invite New Member
                </button>
              ) : (
                <form onSubmit={handleInvite} className="bg-amber-50 rounded-lg p-4">
                  <h3 className="font-semibold text-dark-brown mb-4">Invite Member</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-dark-brown mb-2">
                        Firebase UID
                      </label>
                      <input
                        type="text"
                        value={inviteUid}
                        onChange={(e) => setInviteUid(e.target.value)}
                        placeholder="user_123abc..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-soft-gold"
                      />
                      <p className="text-xs text-dark-gray mt-1">
                        Enter the person's Firebase UID (not email or name)
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-dark-brown mb-2">
                        Role
                      </label>
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-soft-gold"
                      >
                        {AVAILABLE_ROLES.map((role) => (
                          <option key={role} value={role}>
                            {ROLE_LABELS[role]} — {ROLE_DESCRIPTIONS[role]}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setShowInviteForm(false)
                          setInviteUid('')
                        }}
                        className="flex-1 px-4 py-2 border border-gray-300 text-dark-brown rounded-lg hover:bg-gray-50 transition font-medium"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={inviting}
                        className="flex-1 px-4 py-2 bg-soft-gold hover:bg-amber-600 disabled:bg-gray-300 text-white rounded-lg transition font-medium"
                      >
                        {inviting ? 'Inviting...' : 'Send Invitation'}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* Members List */}
          <div>
            <h3 className="font-semibold text-dark-brown mb-4">Members ({members.length})</h3>

            {loading && (
              <div className="text-center py-8">
                <div className="w-4 h-4 rounded-full border-2 border-soft-gold border-t-transparent animate-spin mx-auto" />
              </div>
            )}

            {!loading && members.length === 0 && (
              <p className="text-dark-gray text-center py-8">No members yet</p>
            )}

            {!loading && (
              <div className="space-y-3">
                {members.map((member) => (
                  <div key={member.firebase_uid} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-dark-brown">{maskUid(member.firebase_uid)}</div>
                      <div className="text-xs text-dark-gray mt-1">
                        Joined {new Date(member.joined_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {isLead && member.firebase_uid !== user?.uid && (
                        <select
                          value={member.role}
                          onChange={(e) => handleUpdateRole(member.firebase_uid, e.target.value)}
                          className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:border-soft-gold"
                          title="Change role"
                        >
                          {AVAILABLE_ROLES.map((role) => (
                            <option key={role} value={role}>
                              {ROLE_LABELS[role]}
                            </option>
                          ))}
                        </select>
                      )}

                      {!isLead && (
                        <div className="text-sm font-medium text-dark-brown">
                          {ROLE_LABELS[member.role]}
                        </div>
                      )}

                      {canInvite && member.firebase_uid !== user?.uid && (
                        <button
                          onClick={() => handleRemove(member.firebase_uid)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                          title="Remove member"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Privacy Notice */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-xs text-dark-gray">
                <Shield className="inline mr-1" size={14} />
                <strong>Privacy:</strong> Each person keeps an independent Daanaa profile.
                Joining a context does not share wallets, giving history, or personal data.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
