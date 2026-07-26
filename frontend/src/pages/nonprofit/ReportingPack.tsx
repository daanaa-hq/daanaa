import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { usePageMeta } from '../../hooks/usePageMeta'
import { API_BASE } from '../../data/api'
import LearnMoreLink from '../../components/nonprofit/LearnMoreLink'

interface ReportData {
  organization: { ein: string; name: string }
  dashboard: {
    volunteer_summary: { this_month_hours: number; approved_count: number }
  }
  profile_health?: { completeness_percent: number }
  profile: {
    mission?: string
    website?: string
    donate_url?: string
  }
}

export default function ReportingPack() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  usePageMeta('Export Report | Daanaa', 'Download your organization report.')

  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [exportType, setExportType] = useState<'pdf' | 'csv' | null>(null)

  useEffect(() => {
    if (authLoading || !user) return
    if (!ein) {
      navigate('/nonprofit/my-orgs', { replace: true })
      return
    }

    // Load dashboard data
    Promise.all([
      fetch(`${API_BASE}/api/nonprofit/${ein}/dashboard/overview`).then(r => r.json()),
      fetch(`${API_BASE}/api/public/nonprofit/${ein}/profile/sources`).then(r => r.json())
    ])
      .then(([dashboard, profile]) => {
        setData({
          organization: dashboard.organization,
          dashboard: {
            volunteer_summary: dashboard.volunteer_summary
          },
          profile_health: dashboard.profile_health,
          profile: {
            mission: profile.sources?.mission?.value,
            website: profile.sources?.website?.value,
            donate_url: profile.sources?.donate_url?.value
          }
        })
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Failed to load data'))
      .finally(() => setLoading(false))
  }, [ein, user, authLoading, navigate])

  const generateCSV = () => {
    if (!data) return

    setExporting(true)
    try {
      const rows: string[][] = [
        ['Organization Report'],
        ['Generated', new Date().toISOString()],
        [''],
        ['Organization Name', data.organization.name],
        ['EIN', data.organization.ein],
        [''],
        ...(data.profile_health ? [['Profile Health', data.profile_health.completeness_percent + '%']] : []),
        ['Approved Volunteer Hours (All Time)', String(data.dashboard.volunteer_summary.approved_count)],
        [''],
        ['Mission', data.profile.mission || 'Not set'],
        ['Website', data.profile.website || 'Not set'],
        ['Donation Link', data.profile.donate_url || 'Not set'],
        [''],
        ['Disclaimer', 'Volunteer hours were approved by the nonprofit. Daanaa does not independently verify volunteer submissions.'],
        ['Data Source', 'Daanaa Platform - daanaa.org']
      ]

      const csv = rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${data.organization.name.replace(/\s+/g, '_')}_report_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)

      setExportType('csv')
      setTimeout(() => setExportType(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export CSV')
    } finally {
      setExporting(false)
    }
  }

  const generatePDF = () => {
    if (!data) return

    setExporting(true)
    try {
      // Simple HTML to PDF using browser print
      const html = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Org Report</title>
          <style>
            body { font-family: sans-serif; line-height: 1.6; margin: 40px; color: #333; }
            h1 { color: #1a1a2e; border-bottom: 2px solid #d4af37; padding-bottom: 10px; }
            h2 { color: #1a1a2e; margin-top: 30px; }
            .header { text-align: center; margin-bottom: 40px; }
            .section { margin: 20px 0; }
            .label { font-weight: bold; color: #555; }
            .value { margin-left: 20px; }
            .footer { border-top: 1px solid #ccc; margin-top: 40px; padding-top: 20px; font-size: 12px; color: #777; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>${data.organization.name}</h1>
            <p>EIN: ${data.organization.ein}</p>
            <p>Report Generated: ${new Date().toLocaleDateString()}</p>
          </div>

          <h2>Organization Overview</h2>
          ${data.profile_health ? `
          <div class="section">
            <div class="label">Profile Completeness:</div>
            <div class="value">${data.profile_health.completeness_percent}%</div>
          </div>
          ` : ''}
          <div class="section">
            <div class="label">Approved Volunteer Hours (All Time):</div>
            <div class="value">${data.dashboard.volunteer_summary.approved_count}</div>
          </div>

          <h2>Profile Information</h2>
          <div class="section">
            <div class="label">Mission:</div>
            <div class="value">${data.profile.mission || '(Not provided)'}</div>
          </div>
          <div class="section">
            <div class="label">Website:</div>
            <div class="value"><a href="${data.profile.website}">${data.profile.website || '(Not provided)'}</a></div>
          </div>
          <div class="section">
            <div class="label">Donation Link:</div>
            <div class="value"><a href="${data.profile.donate_url}">${data.profile.donate_url || '(Not provided)'}</a></div>
          </div>

          <div class="footer">
            <p><strong>Important:</strong> Volunteer hours were approved by the nonprofit. Daanaa does not independently verify volunteer submissions.</p>
            <p>This report was generated by Daanaa (daanaa.org), a nonprofit discovery platform. All data is based on public records and nonprofit-supplied information.</p>
          </div>
        </body>
        </html>
      `

      const w = window.open('', '', 'width=800,height=600')
      if (w) {
        w.document.write(html)
        w.document.close()
        w.print()
      }

      setExportType('pdf')
      setTimeout(() => setExportType(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export PDF')
    } finally {
      setExporting(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-deep-navy" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-warm-cream px-6 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-destructive/5 border border-destructive/20 rounded-xl p-6 text-destructive">
            <h2 className="font-display text-lg mb-2">Could not load data</h2>
            <p className="font-body text-body mb-4">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream px-6 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/nonprofit/overview/${ein}`)}
            className="text-soft-gold hover:text-bright-gold font-body text-body font-semibold mb-4"
          >
            ← Back to Dashboard
          </button>
          <h1 className="font-display text-3xl text-deep-navy mb-1">Export Report</h1>
          <p className="font-body text-body text-cool-grey">{data.organization.name}</p>
        </div>

        {/* Preview */}
        <div className="bg-white rounded-2xl shadow-sm p-8 mb-6">
          <h2 className="font-display text-xl text-deep-navy mb-4">Report Preview</h2>

          <div className="space-y-4 font-body text-body">
            <div className="flex justify-between">
              <span className="text-cool-grey">Organization Name:</span>
              <span className="text-deep-navy font-semibold">{data.organization.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-cool-grey">EIN:</span>
              <span className="text-deep-navy font-semibold">{data.organization.ein}</span>
            </div>
            {data.profile_health ? (
              <div className="flex justify-between">
                <span className="text-cool-grey">Profile Completeness:</span>
                <span className="text-deep-navy font-semibold">{data.profile_health.completeness_percent}%</span>
              </div>
            ) : null}
            <div className="flex justify-between">
              <span className="text-cool-grey">Approved Volunteer Hours:</span>
              <span className="text-deep-navy font-semibold">{data.dashboard.volunteer_summary.approved_count}</span>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="font-body text-caption text-blue-900">
              <strong>Note:</strong> This report includes organization overview data, profile information, and volunteer summaries. Volunteer hours are marked as approved by the nonprofit — Daanaa does not independently verify submissions.
            </p>
          </div>
        </div>

        {/* Export Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={generateCSV}
            disabled={exporting}
            className="p-6 rounded-xl bg-white border-2 border-soft-gold text-deep-navy hover:bg-soft-gold/10 disabled:opacity-50 transition"
          >
            <div className="text-3xl mb-2">📊</div>
            <h3 className="font-display text-lg mb-1">Export as CSV</h3>
            <p className="font-body text-caption text-cool-grey">
              Open in Excel or Google Sheets
            </p>
            {exportType === 'csv' && (
              <p className="font-body text-caption text-emerald-600 mt-2">✓ Downloaded</p>
            )}
          </button>

          <button
            onClick={generatePDF}
            disabled={exporting}
            className="p-6 rounded-xl bg-white border-2 border-soft-gold text-deep-navy hover:bg-soft-gold/10 disabled:opacity-50 transition"
          >
            <h3 className="font-display text-lg mb-1">Export as PDF</h3>
            <p className="font-body text-caption text-cool-grey mb-2">
              Print-ready formatted report
            </p>
            {exportType === 'pdf' && (
              <p className="font-body text-caption text-emerald-600 mt-2">Opened</p>
            )}
          </button>
        </div>

        {/* Info */}
        <div className="mt-8 space-y-4">
          <div className="p-4 bg-alert-amber/5 border border-amber-200 rounded-xl">
            <p className="font-body text-small text-amber-900">
              <strong>💾 Reports:</strong> Generate and download reports to share with board members, donors, or for your records. Each report includes a disclaimer that volunteer hours were approved by your organization.
            </p>
          </div>

          <div>
            <LearnMoreLink
              topic="data-freshness"
              text="Learn about report data and freshness"
              onClick={() => window.open('https://daanaa.org/methodology', '_blank')}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
