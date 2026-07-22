import { useEffect, useState } from 'react'
import { API_BASE } from '../../data/api'

interface Edit {
  field: string
  old_value: string
  new_value: string
  date: string
  editor: string
  reason: string
  status: string
}

interface ProfileChangeHistoryProps {
  ein: string
  edits: Edit[]
}

export default function ProfileChangeHistory({ ein, edits }: ProfileChangeHistoryProps) {
  const [allEdits, setAllEdits] = useState<Edit[]>(edits)
  const [loading, setLoading] = useState(edits.length === 0)
  const [error, setError] = useState<string | null>(null)
  const [filterField, setFilterField] = useState<string | null>(null)

  useEffect(() => {
    if (edits.length > 0) return

    fetch(`${API_BASE}/api/nonprofit/${ein}/profile/history`)
      .then(async res => {
        if (!res.ok) throw new Error('Failed to load history')
        return res.json()
      })
      .then(data => setAllEdits(data.changes || []))
      .catch(err => setError(err instanceof Error ? err.message : 'Could not load history'))
      .finally(() => setLoading(false))
  }, [ein, edits])

  const filteredEdits = filterField ? allEdits.filter(e => e.field === filterField) : allEdits
  const uniqueFields = [...new Set(allEdits.map(e => e.field))]

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-deep-navy" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 font-body text-[13px]">
        {error}
      </div>
    )
  }

  if (filteredEdits.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="font-body text-[14px] text-cool-grey">No changes yet. Your profile will show changes as you make them.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Filter */}
      {uniqueFields.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setFilterField(null)}
            className={`px-3 py-1.5 rounded-full font-body text-[12px] font-semibold transition ${
              filterField === null
                ? 'bg-deep-navy text-warm-cream'
                : 'bg-light-grey text-deep-navy hover:bg-light-grey/70'
            }`}
          >
            All Fields
          </button>
          {uniqueFields.map(field => (
            <button
              key={field}
              onClick={() => setFilterField(field)}
              className={`px-3 py-1.5 rounded-full font-body text-[12px] font-semibold transition capitalize ${
                filterField === field
                  ? 'bg-deep-navy text-warm-cream'
                  : 'bg-light-grey text-deep-navy hover:bg-light-grey/70'
              }`}
            >
              {field}
            </button>
          ))}
        </div>
      )}

      {/* Timeline */}
      <div className="relative">
        {filteredEdits.map((edit, idx) => (
          <div key={idx} className="relative pb-8 last:pb-0">
            {/* Timeline line */}
            {idx < filteredEdits.length - 1 && (
              <div className="absolute left-[15px] top-[32px] w-0.5 h-[calc(100%-32px)] bg-light-grey" />
            )}

            {/* Timeline dot */}
            <div className="absolute left-0 top-2 w-8 h-8 rounded-full bg-soft-gold border-4 border-warm-cream flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-deep-navy" />
            </div>

            {/* Content */}
            <div className="ml-16 bg-white rounded-xl p-4 border border-light-grey">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <span className="inline-block px-2.5 py-1 rounded-lg bg-soft-gold/20 text-deep-navy font-body text-[11px] font-semibold capitalize mb-2">
                    {edit.field}
                  </span>
                  <p className="font-body text-[12px] text-cool-grey">
                    {new Date(edit.date).toLocaleDateString()} at {new Date(edit.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>

              {/* Change Details */}
              <div className="space-y-3 my-3">
                <div>
                  <p className="font-body text-[11px] font-semibold text-cool-grey uppercase mb-1">Before</p>
                  <div className="p-2.5 bg-red-50 rounded border border-red-200">
                    <p className="font-body text-[13px] text-deep-navy whitespace-pre-wrap break-words">
                      {edit.old_value || '(empty)'}
                    </p>
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="text-cool-grey">↓</div>
                </div>

                <div>
                  <p className="font-body text-[11px] font-semibold text-cool-grey uppercase mb-1">After</p>
                  <div className="p-2.5 bg-emerald-50 rounded border border-emerald-200">
                    <p className="font-body text-[13px] text-deep-navy whitespace-pre-wrap break-words">
                      {edit.new_value || '(empty)'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Reason & Editor */}
              {edit.reason && (
                <div className="py-2.5 border-t border-light-grey">
                  <p className="font-body text-[11px] font-semibold text-cool-grey uppercase mb-1">Why</p>
                  <p className="font-body text-[13px] text-deep-navy italic">{edit.reason}</p>
                </div>
              )}

              <div className="mt-2 pt-2 border-t border-light-grey">
                <p className="font-body text-[11px] text-cool-grey">
                  Updated by {edit.editor}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p className="font-body text-[13px] text-blue-900">
          <strong>Total changes:</strong> {filteredEdits.length}
          {filterField && ` to ${filterField}`}
        </p>
        <p className="font-body text-[12px] text-blue-700 mt-1">
          All changes are logged and visible to donors. Donors can see when and why your organization updates its profile.
        </p>
      </div>
    </div>
  )
}
