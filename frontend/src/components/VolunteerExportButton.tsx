import React, { useState } from 'react'

interface VolunteerExportButtonProps {
  nonprofitEin: string
  authToken: string
  format?: 'csv' | 'xlsx' | 'pdf'
}

export default function VolunteerExportButton({
  nonprofitEin,
  authToken,
  format = 'csv',
}: VolunteerExportButtonProps) {
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    setLoading(true)
    setError(null)
    setProgress(0)

    try {
      // Initiate export
      const res = await fetch('/api/nonprofit/volunteer-hours/export', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ format }),
      })

      if (!res.ok) throw new Error('Export failed')
      const data = await res.json()
      const jobId = data.job_id

      // Poll for completion
      let completed = false
      let attempts = 0
      const maxAttempts = 300

      while (!completed && attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        attempts++

        const statusRes = await fetch(`/api/nonprofit/background-jobs/${jobId}`, {
          headers: { 'Authorization': `Bearer ${authToken}` },
        })

        if (statusRes.ok) {
          const status = await statusRes.json()
          setProgress(status.progress || 0)

          if (status.status === 'completed') {
            const downloadRes = await fetch(`/api/nonprofit/exports/${jobId}.${format}`, {
              headers: { 'Authorization': `Bearer ${authToken}` },
            })
            const blob = await downloadRes.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `volunteer_hours.${format}`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            completed = true
          } else if (status.status === 'failed') {
            throw new Error(status.error || 'Export failed')
          }
        }
      }

      if (!completed) throw new Error('Export timeout')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
      setProgress(0)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleExport}
        disabled={loading}
        className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700 transition-colors disabled:opacity-50"
      >
        {loading ? `Exporting (${progress}%)...` : `Export as ${format.toUpperCase()}`}
      </button>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {loading && (
        <div className="w-full bg-light-grey rounded-full h-2">
          <div
            className="bg-green-600 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  )
}
