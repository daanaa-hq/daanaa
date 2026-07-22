import React, { useState } from 'react'
import { API_BASE } from '../data/api'

interface VolunteerExportButtonProps {
  nonprofitEin: string
  idToken: string
  format?: 'csv' | 'pdf'
  year?: number
}

export default function VolunteerExportButton({
  nonprofitEin,
  idToken,
  format = 'csv',
  year = new Date().getFullYear(),
}: VolunteerExportButtonProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `${API_BASE}/api/nonprofit/${nonprofitEin}/volunteer/export?year=${year}&format=${format}`,
        { headers: { Authorization: `Bearer ${idToken}` } }
      )
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || 'Export failed')
      }
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `volunteer_hours_${nonprofitEin}_${year}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleExport}
        disabled={loading}
        className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700 transition-colors disabled:opacity-50"
      >
        {loading ? 'Exporting...' : `Export ${year} as ${format.toUpperCase()}`}
      </button>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}
