import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { CheckCircle, XCircle, Edit2, AlertCircle } from 'lucide-react'

interface LinkItem {
  ein: number
  org_name: string
  website?: string
  donate_url: string
  donate_button_text?: string
  volunteer_url: string
  status: 'pending' | 'approved' | 'rejected'
}

interface LinkType {
  label: string
  field: 'website' | 'donate_url' | 'volunteer_url'
  color: string
}

interface Stats {
  pending: number
  approved: number
  rejected: number
  total: number
}

export function VerificationDashboard() {
  const [items, setItems] = useState<LinkItem[]>([])
  const [stats, setStats] = useState<Stats>({ pending: 0, approved: 0, rejected: 0, total: 0 })
  const [loading, setLoading] = useState(false)
  const [editingEin, setEditingEin] = useState<number | null>(null)
  const [editValues, setEditValues] = useState<{ donate: string; volunteer: string }>({ donate: '', volunteer: '' })

  useEffect(() => {
    fetchPending()
    fetchStats()
    const interval = setInterval(() => {
      fetchPending()
      fetchStats()
    }, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchPending = async () => {
    try {
      const response = await fetch('/api/verification/pending?limit=20')
      const data = await response.json()
      setItems(data.items || [])
    } catch (error) {
      console.error('Failed to fetch pending links:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/verification/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const handleApprove = async (ein: number) => {
    setLoading(true)
    try {
      await fetch('/api/verification/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein, verified_by: 'akbar' })
      })
      await fetchPending()
      await fetchStats()
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async (ein: number, reason: string) => {
    setLoading(true)
    try {
      await fetch('/api/verification/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ein, reason: reason || 'Rejected by user' })
      })
      await fetchPending()
      await fetchStats()
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = async (ein: number) => {
    setLoading(true)
    try {
      await fetch('/api/verification/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein,
          donate_url: editValues.donate,
          volunteer_url: editValues.volunteer
        })
      })
      setEditingEin(null)
      await fetchPending()
      await fetchStats()
    } finally {
      setLoading(false)
    }
  }

  const startEdit = (item: LinkItem) => {
    setEditingEin(item.ein)
    setEditValues({
      donate: item.donate_url,
      volunteer: item.volunteer_url
    })
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Link Verification Dashboard</h1>
        <p className="text-gray-600 mt-2">Review and approve discovered donation & volunteer links</p>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending Review</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-yellow-600">{stats.pending}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Approved</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">{stats.approved}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Rejected</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-red-600">{stats.rejected}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.total}</p>
          </CardContent>
        </Card>
      </div>

      {/* Links List */}
      <div className="space-y-4">
        {items.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-gray-500">No links pending review</p>
            </CardContent>
          </Card>
        ) : (
          items.map((item) => (
            <Card key={item.ein} className="border-l-4 border-l-yellow-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{item.org_name}</CardTitle>
                    <CardDescription>EIN: {item.ein}</CardDescription>
                  </div>
                  <Badge variant="secondary">Pending</Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {editingEin === item.ein ? (
                  // Edit Mode
                  <div className="space-y-4 bg-gray-50 p-4 rounded">
                    <div>
                      <label className="text-sm font-medium">Main Website</label>
                      <Input
                        value={item.website || ''}
                        disabled
                        className="mt-1 bg-gray-100"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Donate Link</label>
                      <Input
                        value={editValues.donate}
                        onChange={(e) => setEditValues({ ...editValues, donate: e.target.value })}
                        placeholder="https://..."
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Volunteer Link</label>
                      <Input
                        value={editValues.volunteer}
                        onChange={(e) => setEditValues({ ...editValues, volunteer: e.target.value })}
                        placeholder="https://..."
                        className="mt-1"
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleEdit(item.ein)}
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Save & Approve
                      </Button>
                      <Button
                        onClick={() => setEditingEin(null)}
                        variant="outline"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  // View Mode - Three Link Types
                  <div className="space-y-3">
                    <div className="bg-blue-50 border border-blue-200 p-3 rounded">
                      <p className="text-xs text-blue-700 font-medium">🌐 MAIN WEBSITE</p>
                      {item.website ? (
                        <a href={item.website} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 break-all mt-1 hover:underline">
                          {item.website}
                        </a>
                      ) : (
                        <p className="text-sm text-gray-400 mt-1">(not found)</p>
                      )}
                    </div>

                    <div className="bg-green-50 border border-green-200 p-3 rounded">
                      <p className="text-xs text-green-700 font-medium">💚 DONATE LINK</p>
                      {item.donate_url ? (
                        <>
                          <a href={item.donate_url} target="_blank" rel="noopener noreferrer" className="text-sm text-green-600 break-all mt-1 hover:underline">
                            {item.donate_url}
                          </a>
                          {item.donate_button_text && (
                            <p className="text-xs text-green-600 mt-1">Button text: "{item.donate_button_text}"</p>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-gray-400 mt-1">(not found)</p>
                      )}
                    </div>

                    <div className="bg-purple-50 border border-purple-200 p-3 rounded">
                      <p className="text-xs text-purple-700 font-medium">🤝 VOLUNTEER LINK</p>
                      {item.volunteer_url ? (
                        <a href={item.volunteer_url} target="_blank" rel="noopener noreferrer" className="text-sm text-purple-600 break-all mt-1 hover:underline">
                          {item.volunteer_url}
                        </a>
                      ) : (
                        <p className="text-sm text-gray-400 mt-1">(not found)</p>
                      )}
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button
                        onClick={() => handleApprove(item.ein)}
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700 gap-2 flex-1"
                      >
                        <CheckCircle size={16} /> Approve
                      </Button>
                      <Button
                        onClick={() => startEdit(item)}
                        variant="outline"
                        className="gap-2 flex-1"
                      >
                        <Edit2 size={16} /> Edit
                      </Button>
                      <Button
                        onClick={() => handleReject(item.ein, 'Rejected by user')}
                        disabled={loading}
                        variant="outline"
                        className="text-red-600 hover:text-red-700 flex-1"
                      >
                        <XCircle size={16} /> Reject
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <div className="text-center text-sm text-gray-500">
        <p>⚡ Dashboard auto-refreshes every 5 seconds</p>
      </div>
    </div>
  )
}
