import { useState } from 'react'
import { X } from 'lucide-react'

const CONTEXT_TYPES = [
  { id: 'household', label: '👨‍👩‍👧‍👦 Household', description: 'Coordinate giving with family members' },
  { id: 'daf', label: '💰 DAF or Foundation', description: 'Manage a donor-advised fund or private foundation' },
  { id: 'business', label: '🏢 Business', description: 'Coordinate corporate or business giving' },
  { id: 'other', label: '📋 Other', description: 'Any other shared context' },
]

interface ContextCreatorProps {
  onClose: () => void
  onCreateContext: (contextType: string) => Promise<void>
}

export default function ContextCreator({ onClose, onCreateContext }: ContextCreatorProps) {
  const [selected, setSelected] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!selected) return
    setLoading(true)
    setError(null)
    try {
      await onCreateContext(selected)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create context')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 p-6">
          <h2 className="text-xl font-bold text-dark-brown">Create New Context</h2>
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
          <p className="text-dark-gray mb-6">
            Choose the type of context you want to create:
          </p>

          <div className="space-y-3 mb-6">
            {CONTEXT_TYPES.map((type) => (
              <label
                key={type.id}
                className={`block p-4 rounded-lg border-2 cursor-pointer transition ${
                  selected === type.id
                    ? 'border-soft-gold bg-alert-amber/5'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="context-type"
                  value={type.id}
                  checked={selected === type.id}
                  onChange={() => setSelected(type.id)}
                  className="sr-only"
                />
                <div className="font-semibold text-dark-brown mb-1">{type.label}</div>
                <div className="text-sm text-dark-gray">{type.description}</div>
              </label>
            ))}
          </div>

          {error && (
            <div className="bg-destructive/5 border border-destructive/20 text-destructive px-3 py-2 rounded-lg mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-dark-brown rounded-lg hover:bg-gray-50 transition font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={!selected || loading}
              className="flex-1 px-4 py-2 bg-soft-gold hover:bg-amber-600 disabled:bg-gray-300 text-white rounded-lg transition font-medium"
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
