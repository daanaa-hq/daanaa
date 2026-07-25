import { useState } from 'react'
import { useWallet } from '../contexts/WalletContext'

/**
 * DonorVoice — Qualitative trust signal from donors who've supported an org.
 * Donors who've given can leave one note per org; displayed aggregated, anonymous or named.
 * Stored device-side in wallet; no server sync (privacy-first).
 */
export interface DonorNote {
  id: string
  text: string
  addedAt: number
  authorName?: string
}

export default function DonorVoice({
  ein,
  orgName,
}: {
  ein: string
  orgName: string
}) {
  const { entries } = useWallet()
  const entry = entries.find(e => e.ein === ein)
  const hasDonated = (entry?.donations?.length ?? 0) > 0
  const hasVolunteered = (entry?.volunteerHours?.length ?? 0) > 0
  const canLeaveNote = hasDonated || hasVolunteered

  const [showForm, setShowForm] = useState(false)
  const [note, setNote] = useState('')
  const [authorName, setAuthorName] = useState('')
  const [anonymous, setAnonymous] = useState(true)
  const [notes, setNotes] = useState<DonorNote[]>(entry?.donorNotes || [])

  const handleSubmit = () => {
    if (!note.trim()) return

    const newNote: DonorNote = {
      id: Math.random().toString(36).slice(2, 11),
      text: note.trim(),
      addedAt: Date.now(),
      authorName: anonymous ? undefined : authorName.trim() || undefined,
    }

    setNotes(prev => [newNote, ...prev])
    setNote('')
    setAuthorName('')
    setShowForm(false)

    // TODO: Save to wallet entry (walletContext update needed)
  }

  const recentNotes = notes.slice(0, 3)
  const hasMore = notes.length > 3

  if (!canLeaveNote && notes.length === 0) {
    return null
  }

  return (
    <div className="rounded-xl border border-soft-gold/20 bg-warm-cream/40 p-6">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold text-deep-navy text-[14px] mb-1">What supporters say</h3>
          <p className="font-body text-[12px] text-cool-grey">
            {notes.length === 0
              ? 'Be the first to share'
              : `${notes.length} supporter${notes.length === 1 ? '' : 's'} have shared notes`}
          </p>
        </div>
        {canLeaveNote && !showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-3 py-1.5 bg-soft-gold text-deep-navy rounded-lg font-body text-[12px] font-semibold hover:bg-bright-gold transition-colors shrink-0"
          >
            Add note
          </button>
        )}
      </div>

      {/* Note form */}
      {showForm && canLeaveNote && (
        <div className="mb-4 p-4 bg-white rounded-lg border border-light-grey space-y-3">
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Share what impressed you or what to know about {orgName}..."
            maxLength={200}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-[13px] focus:outline-none focus:ring-2 focus:ring-soft-gold/40 resize-none"
            rows={3}
          />

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer flex-1">
              <input
                type="checkbox"
                checked={anonymous}
                onChange={() => setAnonymous(!anonymous)}
                className="rounded"
              />
              <span className="font-body text-[12px] text-cool-grey">Stay anonymous</span>
            </label>

            {!anonymous && (
              <input
                type="text"
                value={authorName}
                onChange={e => setAuthorName(e.target.value)}
                placeholder="Your first name"
                maxLength={50}
                className="flex-1 px-3 py-2 border border-light-grey rounded-lg font-body text-[12px] focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              />
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={!note.trim()}
              className="px-4 py-2 bg-soft-gold text-deep-navy rounded-lg font-body text-[12px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Post note
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 text-cool-grey font-body text-[12px] hover:text-deep-navy transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Notes list */}
      {recentNotes.length > 0 && (
        <div className="space-y-2">
          {recentNotes.map(n => (
            <div key={n.id} className="bg-white rounded-lg p-3 border border-light-cream">
              <p className="font-body text-[13px] text-deep-navy leading-relaxed">{n.text}</p>
              <p className="mt-1.5 font-body text-[11px] text-muted-cream">
                {n.authorName ? `— ${n.authorName}` : '— Anonymous'} · {new Date(n.addedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </p>
            </div>
          ))}

          {hasMore && (
            <button className="w-full text-center text-soft-gold hover:text-bright-gold font-body text-[12px] py-2 transition-colors">
              Show all {notes.length} notes
            </button>
          )}
        </div>
      )}

      {canLeaveNote && notes.length === 0 && !showForm && (
        <p className="font-body text-[12px] text-cool-grey text-center py-4">
          You've supported this org. What was your experience?
        </p>
      )}
    </div>
  )
}
