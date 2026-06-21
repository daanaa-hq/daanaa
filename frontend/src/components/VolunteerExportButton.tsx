import React, { useState } from 'react'
import { BackgroundJobSchema, ExportInitiationSchema, type BackgroundJob, type ExportInitiation } from '../lib/schemas'

interface VolunteerExportButtonProps {
  nonprofitEin: string
  authToken: string
  format?: 'csv' | 'xlsx'
}

/**
 * VolunteerExportButton
 *
 * Initiates and tracks async CSV export of volunteer hours:
 * 1. POST /api/nonprofit/volunteer-hours/export → get job_id
 * 2. Poll /api/nonprofit/background-jobs/{job_id} every 1 second
 * 3. Show progress states: "Generating..." → "Ready! Downloading..."
 * 4. Auto-download when status='complete'
 * 5. Timeout after 60 seconds with error message
 *
 * Props:
 *   - nonprofitEin: EIN for API auth
 *   - authToken: Bearer token
 *   - format: Export format (default: 'csv')
 */
export default function VolunteerExportButton({
  nonprofitEin,
  authToken,
  format = 'csv',
}: VolunteerExportButtonProps) {
  const [exporting, setExporting] = useState(false)
  const [progress, setProgress] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    setError(null)
    setProgress('Initiating export...')
    setExporting(true)

    try {
      // Step 1: Start export
      const initiateResponse = await fetch(`/api/nonprofit/volunteer-hours/export?format=${format}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!initiateResponse.ok) {
        throw new Error('Failed to start export')
      }

      const initiateData = await initiateResponse.json()
      const { job_id } = ExportInitiationSchema.parse(initiateData)

      // Step 2: Poll job status
      setProgress('Generating CSV...')
      let job: BackgroundJob | null = null
      let pollCount = 0
      const maxPolls = 60 // 60 seconds timeout

      while (pollCount < maxPolls) {
        const statusResponse = await fetch(`/api/nonprofit/background-jobs/${job_id}`, {
          headers: {
            Authorization: `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        })

        if (!statusResponse.ok) {
          throw new Error('Failed to check job status')
        }

        const statusData = await statusResponse.json()
        job = BackgroundJobSchema.parse(statusData)

        if (job.status === 'complete') {
          setProgress('Ready! Downloading...')
          break
        }

        if (job.status === 'failed') {
          throw new Error(job.error_message || 'Export failed on server')
        }

        // Wait 1 second before polling again
        await new Promise(resolve => setTimeout(resolve, 1000))
        pollCount++
      }

      if (pollCount >= maxPolls) {
        throw new Error('Export is taking too long. Please try again.')
      }

      if (!job || job.status !== 'complete') {
        throw new Error('Export did not complete')
      }

      // Step 3: Download file
      if (job.download_link) {
        setProgress('Downloading...')
        const link = document.createElement('a')
        link.href = job.download_link
        link.download = `volunteer_hours_${nonprofitEin}_${job_id.slice(0, 8)}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        setProgress(null)
        setExporting(false)
      }
    } catch (err) {
      const errorMsg = (err as Error).message || 'Export failed'
      setError(errorMsg)
      setProgress(null)
      setExporting(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleExport}
        disabled={exporting}
        className="px-4 py-2 bg-cool-grey text-white rounded-lg font-semibold text-sm hover:bg-cool-grey/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 justify-center"
      >
        {exporting ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            {progress || 'Exporting...'}
          </>
        ) : (
          <>
            <span>📥</span>
            Export Hours
          </>
        )}
      </button>

      {error && (
        <div className="text-xs text-red-600 bg-red-50 rounded px-3 py-2 border border-red-200">
          {error}
        </div>
      )}
    </div>
  )
}
