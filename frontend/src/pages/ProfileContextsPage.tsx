import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useProfileContexts } from '../hooks/useProfileContexts'
import ContextCreator from '../components/profile-contexts/ContextCreator'
import ContextList from '../components/profile-contexts/ContextList'
import PendingInvitations from '../components/profile-contexts/PendingInvitations'
import MemberManagement from '../components/profile-contexts/MemberManagement'

const CONTEXT_LABELS = {
  household: '👨‍👩‍👧‍👦 Household',
  daf: '💰 DAF or Foundation',
  business: '🏢 Business',
  other: '📋 Other',
}

export default function ProfileContextsPage() {
  const { user } = useAuth()
  const {
    contexts,
    loading,
    error,
    fetchContexts,
    createContext,
    getMembers,
    inviteMember,
    updateMemberRole,
    removeMember,
    getPendingInvitations,
    acceptInvitation,
    rejectInvitation,
    archiveContext,
  } = useProfileContexts()

  const [showCreator, setShowCreator] = useState(false)
  const [selectedContextId, setSelectedContextId] = useState<string | null>(null)
  const [showMemberManagement, setShowMemberManagement] = useState(false)

  // Feature flag check
  const featureFlagEnabled = import.meta.env.VITE_ENABLE_PROFILE_CONTEXTS === 'true'
  if (!featureFlagEnabled) {
    return (
      <div className="min-h-screen bg-soft-cream flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
          <h1 className="text-2xl font-bold text-dark-brown mb-4">Profile Contexts</h1>
          <p className="text-dark-gray">This feature is not yet available.</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-soft-cream flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
          <h1 className="text-2xl font-bold text-dark-brown mb-4">Profile Contexts</h1>
          <p className="text-dark-gray">Please log in to manage your profile contexts.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-soft-cream py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-dark-brown mb-2">Profile Contexts</h1>
          <p className="text-dark-gray">
            Manage shared giving contexts with household members, DAFs, business teams, and more.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Pending Invitations Section */}
        <div className="mb-8">
          <PendingInvitations
            getPendingInvitations={getPendingInvitations}
            acceptInvitation={acceptInvitation}
            rejectInvitation={rejectInvitation}
            onActionComplete={fetchContexts}
          />
        </div>

        {/* Create Context Button */}
        <div className="mb-8">
          <button
            onClick={() => setShowCreator(true)}
            className="bg-soft-gold hover:bg-amber-600 text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            + Create New Context
          </button>
        </div>

        {/* Context Creator Dialog */}
        {showCreator && (
          <ContextCreator
            onClose={() => setShowCreator(false)}
            onCreateContext={async (contextType) => {
              await createContext(contextType)
              setShowCreator(false)
            }}
          />
        )}

        {/* Contexts List */}
        <div className="space-y-6">
          {loading && (
            <div className="text-center py-8">
              <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin mx-auto" />
            </div>
          )}

          {!loading && contexts.length === 0 && (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-dark-gray mb-4">No contexts yet. Create one to get started!</p>
            </div>
          )}

          {!loading && contexts.map((context) => (
            <ContextList
              key={context.context_id}
              context={context}
              onManageMembers={(contextId) => {
                setSelectedContextId(contextId)
                setShowMemberManagement(true)
              }}
              onArchive={archiveContext}
            />
          ))}
        </div>

        {/* Member Management Modal */}
        {showMemberManagement && selectedContextId && (
          <MemberManagement
            contextId={selectedContextId}
            context={contexts.find(c => c.context_id === selectedContextId)!}
            onClose={() => {
              setShowMemberManagement(false)
              setSelectedContextId(null)
            }}
            getMembers={getMembers}
            inviteMember={inviteMember}
            updateMemberRole={updateMemberRole}
            removeMember={removeMember}
            onMembersUpdated={fetchContexts}
          />
        )}
      </div>
    </div>
  )
}
