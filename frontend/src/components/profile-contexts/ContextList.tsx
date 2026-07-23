import { Users, Archive, Settings } from 'lucide-react'
import type { ProfileContext } from '../../hooks/useProfileContexts'

const CONTEXT_LABELS: Record<string, string> = {
  household: '👨‍👩‍👧‍👦 Household',
  daf: '💰 DAF or Foundation',
  business: '🏢 Business',
  other: '📋 Other',
}

const ROLE_LABELS: Record<string, string> = {
  lead: '👑 Lead',
  support: '🤝 Support',
  member: '👤 Member',
  viewer: '👁️ Viewer',
}

const ROLE_DESCRIPTIONS: Record<string, string> = {
  lead: 'Full control',
  support: 'Can invite & remove',
  member: 'Read-only',
  viewer: 'View-only',
}

interface ContextListProps {
  context: ProfileContext
  onManageMembers: (contextId: string) => void
  onArchive: (contextId: string) => Promise<void>
}

export default function ContextList({ context, onManageMembers, onArchive }: ContextListProps) {
  const canManage = context.role === 'lead' || context.role === 'support'
  const isArchived = context.status === 'archived'

  const handleArchive = async () => {
    if (confirm('Are you sure you want to archive this context?')) {
      try {
        await onArchive(context.context_id)
      } catch (err) {
        alert(`Failed to archive context: ${err instanceof Error ? err.message : 'Unknown error'}`)
      }
    }
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${isArchived ? 'opacity-75' : ''}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="text-2xl">{CONTEXT_LABELS[context.context_type]}</div>
            {isArchived && (
              <span className="inline-block bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
                Archived
              </span>
            )}
          </div>
          <p className="text-dark-gray text-sm">
            Created {new Date(context.created_at).toLocaleDateString()}
          </p>
        </div>
        {canManage && !isArchived && (
          <button
            onClick={() => onManageMembers(context.context_id)}
            className="ml-4 p-2 text-soft-gold hover:bg-amber-50 rounded-lg transition"
            title="Manage members"
          >
            <Settings size={20} />
          </button>
        )}
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-6 mb-4">
        <div className="flex items-center gap-2">
          <Users size={18} className="text-dark-gray" />
          <span className="text-dark-gray">
            {context.member_count} {context.member_count === 1 ? 'member' : 'members'}
          </span>
        </div>
        <div className="text-dark-gray">
          <span className="font-semibold">{ROLE_LABELS[context.role]}</span>
          <span className="text-sm ml-1">({ROLE_DESCRIPTIONS[context.role]})</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        {canManage && !isArchived && (
          <>
            <button
              onClick={() => onManageMembers(context.context_id)}
              className="flex-1 px-4 py-2 bg-soft-gold hover:bg-amber-600 text-white rounded-lg transition font-medium text-sm"
            >
              Manage Members
            </button>
            {context.role === 'lead' && (
              <button
                onClick={handleArchive}
                className="px-4 py-2 border border-gray-300 text-dark-gray hover:bg-gray-50 rounded-lg transition font-medium text-sm flex items-center gap-2"
              >
                <Archive size={16} />
                Archive
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
