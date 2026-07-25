import React, { useState, useEffect } from 'react'

interface MessageEvent {
  id: string
  event_type: string
  event_timestamp: string
  ip_address?: string
  user_agent?: string
}

interface DonorMessageTimelineProps {
  messageId: string
  authToken: string
  onClose: () => void
}

export default function DonorMessageTimeline({
  messageId,
  authToken,
  onClose,
}: DonorMessageTimelineProps) {
  const [events, setEvents] = useState<MessageEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await fetch(`/api/nonprofit/donor-messages/${messageId}/events`, {
          headers: { 'Authorization': `Bearer ${authToken}` },
        })
        if (!res.ok) throw new Error('Failed to load events')
        const data = await res.json()
        setEvents(data.events || [])
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    fetchEvents()
  }, [messageId, authToken])

  const eventLabel: Record<string, string> = {
    open: 'Opened',
    click: 'Clicked',
    bounce: 'Bounced',
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-display text-2xl text-deep-navy">Message Timeline</h2>
          <button onClick={onClose} className="text-2xl text-cool-grey hover:text-deep-navy">
            ✕
          </button>
        </div>

        {loading && <p className="text-center text-cool-grey">Loading events...</p>}
        {error && <p className="text-center text-red-600 text-sm">{error}</p>}

        {!loading && events.length === 0 && (
          <p className="text-center text-cool-grey">No events recorded</p>
        )}

        {!loading && events.length > 0 && (
          <div className="space-y-4">
            {events.map((event, idx) => (
              <div key={event.id} className="pb-3 border-b border-light-grey">
                <p className="font-semibold text-sm text-deep-navy capitalize">
                  {eventLabel[event.event_type] || event.event_type}
                </p>
                <p className="text-xs text-cool-grey mt-1">
                  {new Date(event.event_timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
