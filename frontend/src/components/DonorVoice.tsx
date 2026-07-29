import { useState } from 'react'
import { useWallet } from '../contexts/WalletContext'
import { CardPattern } from './ui/CardPattern'

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

  const { addDonorNote } = useWallet()

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

    // Save to wallet entry
    addDonorNote(ein, newNote)
  }

  const recentNotes = notes.slice(0, 3)
  const hasMore = notes.length > 3

  if (!canLeaveNote && notes.length === 0) {
    return null
  }

  return (
    <CardPattern variant="subtle">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold text-deep-navy text-body mb-1">What supporters say</h3>
          <p className="font-body text-caption text-cool-grey">
            {notes.length === 0
              ? 'Be the first to share'
              : `${notes.length} supporter${notes.length === 1 ? '' : 's'} have shared notes`}
          </p>
        </div>
        {canLeaveNote && !showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-3 py-1.5 bg-soft-gold text-deep-navy rounded-lg font-body text-caption font-semibold hover:bg-bright-gold transition-colors shrink-0"
          >
            Add note
          </button>
        )}
      </div>

      {/* Note form */}
      {showForm && canLeaveNote && (
        <CardPattern variant="nested" className="mb-4 space-y-3">
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Share what impressed you or what to know about {orgName}..."
            maxLength={200}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-small focus:outline-none focus:ring-2 focus:ring-soft-gold/40 resize-none"
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
              <span className="font-body text-caption text-cool-grey">Stay anonymous</span>
            </label>

            {!anonymous && (
              <input
                type="text"
                value={authorName}
                onChange={e => setAuthorName(e.target.value)}
                placeholder="Your first name"
                maxLength={50}
                className="flex-1 px-3 py-2 border border-light-grey rounded-lg font-body text-caption focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              />
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={!note.trim()}
              className="px-4 py-2 bg-soft-gold text-deep-navy rounded-lg font-body text-caption font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Post note
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 text-cool-grey font-body text-caption hover:text-deep-navy transition-colors"
            >
              Cancel
            </button>
          </div>
        </CardPattern>
      )}

      {/* Notes list */}
      {recentNotes.length > 0 && (
        <div className="space-y-2">
          {recentNotes.map(n => (
            <CardPattern key={n.id} variant="default">
              <p className="font-body text-small text-deep-navy leading-relaxed">{n.text}</p>
              <p className="mt-1.5 font-body text-label text-muted-cream">
                {n.authorName ? `— ${n.authorName}` : '— Anonymous'} · {new Date(n.addedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </p>
            </CardPattern>
          ))}

          {hasMore && (
            <button className="w-full text-center text-soft-gold hover:text-bright-gold font-body text-caption py-2 transition-colors">
              Show all {notes.length} notes
            </button>
          )}
        </div>
      )}

      {canLeaveNote && notes.length === 0 && !showForm && (
        <p className="font-body text-caption text-cool-grey text-center py-4">
          You've supported this org. What was your experience?
        </p>
      )}
    </CardPattern>
  )
}
