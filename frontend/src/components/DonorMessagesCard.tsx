import React, { useState, useEffect } from 'react'
import { CardPattern } from './ui/CardPattern'

interface DonorMessage {
  id: string
  donor_email: string
  donor_name: string
  message_subject: string
  delivery_status: string
  sent_at: string
  open_count: number
  link_clicks: number
}

interface DonorMessagesCardProps {
  nonprofitEin: string
  authToken: string
}

export default function DonorMessagesCard({
  nonprofitEin,
  authToken,
}: DonorMessagesCardProps) {
  const [messages, setMessages] = useState<DonorMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showComposer, setShowComposer] = useState(false)

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await fetch('/api/nonprofit/donor-messages?limit=5', {
          headers: { 'Authorization': `Bearer ${authToken}` },
        })
        if (!res.ok) throw new Error('Failed to load messages')
        const data = await res.json()
        setMessages(data.messages || [])
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    fetchMessages()
  }, [authToken])

  if (loading) {
    return <CardPattern variant="elevated" className="text-center">Loading messages...</CardPattern>
  }

  return (
    <CardPattern variant="gradient">
      <div className="flex items-start justify-between mb-4">
        <h3 className="font-display text-xl text-deep-navy">Donor Communication</h3>
        <span className="text-2xl">💌</span>
      </div>

      {error && (
        <p className="text-sm text-destructive mb-4">{error}</p>
      )}

      <div className="space-y-3 mb-4">
        {messages.length === 0 ? (
          <p className="text-sm text-cool-grey">No messages sent yet</p>
        ) : (
          messages.map((msg) => (
            <CardPattern key={msg.id} variant="nested">
              <p className="font-semibold text-deep-navy">{msg.donor_name}</p>
              <p className="text-xs text-cool-grey mt-1">{msg.message_subject}</p>
              <div className="flex gap-4 mt-2 text-xs text-cool-grey">
                <span>Opens: {msg.open_count}</span>
                <span>Clicks: {msg.link_clicks}</span>
              </div>
            </CardPattern>
          ))
        )}
      </div>

      <button
        onClick={() => setShowComposer(true)}
        className="w-full px-4 py-2 bg-default text-white rounded-lg font-semibold text-sm hover:opacity-90 transition-colors"
      >
        Compose Message
      </button>
    </CardPattern>
  )
}
