import React, { useState, useEffect } from 'react'
import { usePageMeta } from '../../hooks/usePageMeta'
import { useParams, useNavigate } from 'react-router-dom'

interface LetterRequest {
  id: string
  donor_name: string
  amount: number
  donation_date: string
  status: 'pending' | 'approved' | 'generated'
}

interface DashboardData {
  nonprofit_ein: string
  name: string
  pending_letters: LetterRequest[]
  letters_remaining: number
}

export default function NonprofitDashboardPage() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  usePageMeta('Nonprofit Dashboard | Daanaa', 'Manage donation letter requests, approvals, and credits')

  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [approving, setApproving] = useState<string | null>(null)

  const getAuthToken = () => {
    return localStorage.getItem('nonprofit_account_id') || localStorage.getItem('nonprofit_auth_token') || ein || ''
  }

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const authToken = getAuthToken()
        if (!authToken) {
          navigate('/nonprofit/letters/signup')
          return
        }

        const res = await fetch('/api/nonprofit/dashboard', {
          headers: { Authorization: `Bearer ${authToken}` },
        })
        if (!res.ok) throw new Error('Failed to load dashboard')
        const data = await res.json()
        setDashboard(data)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [ein, navigate])

  const handleApprove = async (letterId: string) => {
    setApproving(letterId)
    try {
      const authToken = getAuthToken()
      const res = await fetch(`/api/nonprofit/letter/${letterId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (!res.ok) throw new Error('Failed to approve letter')
      setDashboard(prev => prev ? {
        ...prev,
        pending_letters: prev.pending_letters.map(l =>
          l.id === letterId ? { ...l, status: 'approved' } : l
        )
      } : null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setApproving(null)
    }
  }

  const handleGenerateLetter = async (letterId: string) => {
    try {
      const authToken = getAuthToken()
      const res = await fetch(`/api/nonprofit/letter/${letterId}/generate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
      })
      if (!res.ok) throw new Error('Failed to generate letter')

      // Handle PDF download
      const contentType = res.headers.get('content-type')
      if (contentType?.includes('application/pdf')) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `donation_letter_${letterId}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        const data = await res.json()
        if (data.pdf_url) window.open(data.pdf_url, '_blank')
      }

      setDashboard(prev => prev ? {
        ...prev,
        pending_letters: prev.pending_letters.map(l =>
          l.id === letterId ? { ...l, status: 'generated' } : l
        ),
        letters_remaining: prev.letters_remaining - 1
      } : null)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (loading) return <div className="p-8 text-center">Loading...</div>
  if (error) return <div className="p-8 text-center text-red-600">{error}</div>
  if (!dashboard) return <div className="p-8 text-center">No data</div>

  return (
    <div className="min-h-screen bg-soft-cream p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-4xl italic text-deep-navy mb-2">{dashboard.name}</h1>
          <p className="text-cool-grey">EIN: {dashboard.nonprofit_ein}</p>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm mb-8 border-l-4 border-soft-gold">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-cool-grey font-semibold mb-1">Letter Credits</p>
              <p className="font-display text-4xl italic text-deep-navy">{dashboard.letters_remaining}</p>
              <p className="text-xs text-cool-grey mt-2">letters remaining</p>
            </div>
            <button className="px-4 py-2 bg-soft-gold text-deep-navy rounded-lg font-semibold text-sm hover:bg-bright-gold transition-colors">
              Buy More
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="font-display text-2xl italic text-deep-navy mb-6">
            Pending Requests ({dashboard.pending_letters.length})
          </h2>

          {dashboard.pending_letters.length === 0 ? (
            <p className="text-center text-cool-grey py-8">No pending requests</p>
          ) : (
            <div className="space-y-4">
              {dashboard.pending_letters.map(letter => (
                <div key={letter.id} className="border border-light-grey rounded-lg p-4 hover:bg-soft-cream">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <p className="font-semibold text-deep-navy">{letter.donor_name}</p>
                      <p className="text-sm text-cool-grey">${letter.amount.toFixed(2)}</p>
                      <p className="text-xs text-cool-grey">{letter.donation_date}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      letter.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      letter.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {letter.status}
                    </span>
                  </div>

                  {letter.status === 'pending' && (
                    <div className="flex gap-2">
                      <button onClick={() => handleApprove(letter.id)} disabled={approving === letter.id}
                        className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50">
                        {approving === letter.id ? 'Approving...' : 'Approve'}
                      </button>
                      <button className="flex-1 px-3 py-2 border border-light-grey text-deep-navy rounded-lg text-sm font-semibold hover:bg-soft-cream">
                        Reject
                      </button>
                    </div>
                  )}

                  {letter.status === 'approved' && (
                    <button onClick={() => handleGenerateLetter(letter.id)}
                      className="w-full px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-semibold hover:bg-green-700">
                      Generate Letter
                    </button>
                  )}

                  {letter.status === 'generated' && (
                    <p className="text-sm text-green-700 font-semibold">✓ Generated</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
