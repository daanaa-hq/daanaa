import { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useWallet } from '../contexts/WalletContext'
import { usePageMeta } from '../hooks/usePageMeta'
import {
  exportWalletAsJSON, exportWalletAsCSV, downloadFile, deleteWalletData, getDeleteSummary
} from '../utils/walletExport'

// Mini preview of each theme: a tiny mock page (header bar, text lines, gold
// accent) rendered in that theme's actual colors, so the user sees what they
// are choosing before they click.
function ThemePreview({ mode, active, onSelect }: {
  mode: 'dark' | 'light'
  active: boolean
  onSelect: () => void
}) {
  const c = mode === 'dark'
    ? { page: '#0A1628', card: '#111D2E', line: '#F5F0EB', sub: '#D4CCBF', accent: '#C9A96E' }
    : { page: '#F8F7F5', card: '#FFFFFF', line: '#1E2530', sub: '#6B6257', accent: '#8B6F47' }

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      aria-label={`Use ${mode} theme`}
      className={`group flex-1 rounded-xl border-2 p-3 text-left transition-all duration-150 ${
        active
          ? 'border-soft-gold shadow-[0_0_0_3px_rgb(var(--soft-gold-rgb)/0.15)]'
          : 'border-navy-mid hover:border-soft-gold/50'
      }`}
    >
      {/* Mock page */}
      <div className="rounded-lg overflow-hidden border" style={{ background: c.page, borderColor: mode === 'dark' ? '#1A2744' : '#E5E0D8' }}>
        <div className="h-5 flex items-center gap-1 px-2" style={{ background: c.card }}>
          <span className="w-8 h-1.5 rounded-full" style={{ background: c.accent }} />
          <span className="ml-auto w-4 h-1.5 rounded-full opacity-40" style={{ background: c.line }} />
        </div>
        <div className="p-2.5 space-y-1.5">
          <span className="block w-3/4 h-2 rounded-full" style={{ background: c.line }} />
          <span className="block w-full h-1.5 rounded-full opacity-70" style={{ background: c.sub }} />
          <span className="block w-2/3 h-1.5 rounded-full opacity-70" style={{ background: c.sub }} />
          <div className="flex gap-1.5 pt-1">
            <span className="w-10 h-3 rounded-full" style={{ background: c.accent }} />
            <span className="w-10 h-3 rounded-full border" style={{ borderColor: c.sub, opacity: 0.6 }} />
          </div>
        </div>
      </div>

      {/* Label row */}
      <div className="mt-3 flex items-center justify-between px-0.5">
        <span className="font-body text-[14px] font-medium text-warm-cream capitalize">{mode}</span>
        <span
          className={`inline-flex items-center justify-center w-[18px] h-[18px] rounded-full border-2 transition-colors ${
            active ? 'border-soft-gold bg-soft-gold' : 'border-muted-cream/50'
          }`}
        >
          {active && (
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#0A1628" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
        </span>
      </div>
    </button>
  )
}

/**
 * Export wallet modal: pick format, preview size, download.
 */
function ExportModal({ entries, onClose }: { entries: any[]; onClose: () => void }) {
  const [format, setFormat] = useState<'json' | 'csv'>('json')
  const [exported, setExported] = useState(false)

  const handleExport = () => {
    const now = new Date().toISOString().split('T')[0]
    const content = format === 'json' ? exportWalletAsJSON(entries) : exportWalletAsCSV(entries)
    const filename = `daanaa-wallet-${now}.${format === 'json' ? 'json' : 'csv'}`
    downloadFile(content, filename, format === 'json' ? 'application/json' : 'text/csv')
    setExported(true)
  }

  if (exported) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-dark-surface rounded-2xl border border-navy-mid max-w-sm w-full p-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-soft-gold/15 mx-auto mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h3 className="font-body text-center text-warm-cream font-semibold mb-2">Download complete</h3>
          <p className="text-center text-muted-cream text-sm mb-6">
            Your wallet data ({entries.length} org{entries.length !== 1 ? 's' : ''}) is ready on your device.
          </p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2.5 rounded-lg bg-soft-gold/15 text-soft-gold hover:bg-soft-gold/25 transition-colors font-body text-sm font-medium"
          >
            Done
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-surface rounded-2xl border border-navy-mid max-w-sm w-full p-6">
        <h3 className="font-body text-warm-cream font-semibold text-lg mb-2">Export your wallet</h3>
        <p className="text-muted-cream text-sm mb-4">
          Download your {entries.length} org{entries.length !== 1 ? 's' : ''} with all bookmarks and giving intent.
        </p>

        <div className="space-y-3 mb-6">
          <label className="flex items-center gap-3 p-3 rounded-lg border border-navy-mid hover:border-soft-gold/40 cursor-pointer transition-colors">
            <input
              type="radio"
              value="json"
              checked={format === 'json'}
              onChange={(e) => setFormat(e.target.value as 'json' | 'csv')}
              className="w-4 h-4"
            />
            <div>
              <p className="font-body text-sm font-medium text-warm-cream">JSON (machine-readable)</p>
              <p className="text-xs text-muted-cream">Portable, includes all data</p>
            </div>
          </label>

          <label className="flex items-center gap-3 p-3 rounded-lg border border-navy-mid hover:border-soft-gold/40 cursor-pointer transition-colors">
            <input
              type="radio"
              value="csv"
              checked={format === 'csv'}
              onChange={(e) => setFormat(e.target.value as 'json' | 'csv')}
              className="w-4 h-4"
            />
            <div>
              <p className="font-body text-sm font-medium text-warm-cream">CSV (spreadsheet)</p>
              <p className="text-xs text-muted-cream">Opens in Excel or Sheets</p>
            </div>
          </label>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-lg border border-navy-mid text-muted-cream hover:text-warm-cream transition-colors font-body text-sm font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            className="flex-1 px-4 py-2.5 rounded-lg bg-soft-gold text-deep-navy hover:bg-bright-gold transition-colors font-body text-sm font-medium"
          >
            Export
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Delete wallet modal: strong confirmation with summary of what's lost.
 */
function DeleteModal({ entries, onClose }: { entries: any[]; onClose: () => void }) {
  const [step, setStep] = useState<'confirm' | 'final' | 'done'>('confirm')
  const summary = getDeleteSummary(entries)

  const handleConfirm = () => setStep('final')
  const handleDelete = () => {
    deleteWalletData()
    setStep('done')
  }

  if (step === 'done') {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-dark-surface rounded-2xl border border-navy-mid max-w-sm w-full p-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-alert-amber/15 mx-auto mb-4">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-alert-amber">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h3 className="font-body text-center text-warm-cream font-semibold mb-2">Wallet deleted</h3>
          <p className="text-center text-muted-cream text-sm mb-6">
            All {entries.length} nonprofit{entries.length !== 1 ? 's' : ''} and activity logs have been permanently removed from this device.
          </p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2.5 rounded-lg bg-alert-amber/15 text-alert-amber hover:bg-alert-amber/25 transition-colors font-body text-sm font-medium"
          >
            Done
          </button>
        </div>
      </div>
    )
  }

  if (step === 'final') {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-dark-surface rounded-2xl border border-navy-mid max-w-sm w-full p-6">
          <h3 className="font-body text-warm-cream font-semibold text-lg mb-4">This cannot be undone</h3>
          <div className="space-y-2 mb-6 p-4 rounded-lg bg-alert-amber/10 border border-alert-amber/30">
            <p className="font-body text-sm text-alert-amber font-medium">You are about to permanently delete:</p>
            <ul className="text-sm text-alert-amber/80 space-y-1 font-body">
              <li>• {summary.bookmarks} saved nonprofit{summary.bookmarks !== 1 ? 's' : ''}</li>
              {summary.donations > 0 && <li>• {summary.donations} donation log{summary.donations !== 1 ? 's' : ''}</li>}
              {summary.volunteerRecords > 0 && <li>• {summary.volunteerRecords} volunteer record{summary.volunteerRecords !== 1 ? 's' : ''}</li>}
              <li>• All metadata and timestamps</li>
            </ul>
          </div>
          <p className="text-muted-cream text-xs mb-6">
            If you exported first, you can re-import your data later. Otherwise, this data is gone forever.
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setStep('confirm')}
              className="flex-1 px-4 py-2.5 rounded-lg border border-navy-mid text-muted-cream hover:text-warm-cream transition-colors font-body text-sm font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              className="flex-1 px-4 py-2.5 rounded-lg bg-alert-amber text-deep-navy hover:bg-orange-600 transition-colors font-body text-sm font-medium"
            >
              Delete forever
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-surface rounded-2xl border border-navy-mid max-w-sm w-full p-6">
        <h3 className="font-body text-warm-cream font-semibold text-lg mb-2">Delete all wallet data?</h3>
        <p className="text-muted-cream text-sm mb-4">
          This will remove {summary.bookmarks} saved nonprofit{summary.bookmarks !== 1 ? 's' : ''} and {summary.donations + summary.volunteerRecords} activity record{summary.donations + summary.volunteerRecords !== 1 ? 's' : ''}.
        </p>
        <p className="text-muted-cream text-xs mb-6">
          💡 Tip: Export your data first if you might want it back.
        </p>
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-lg border border-navy-mid text-muted-cream hover:text-warm-cream transition-colors font-body text-sm font-medium"
          >
            Keep it
          </button>
          <button
            onClick={handleConfirm}
            className="flex-1 px-4 py-2.5 rounded-lg bg-alert-amber/20 text-alert-amber hover:bg-alert-amber/30 transition-colors font-body text-sm font-medium"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme()
  const { entries } = useWallet()
  const [exportModal, setExportModal] = useState(false)
  const [deleteModal, setDeleteModal] = useState(false)

  usePageMeta(
    'Settings | Daanaa',
    'Customize your Daanaa experience'
  )

  const select = (mode: 'dark' | 'light') => {
    if (mode !== theme) toggleTheme()
  }

  return (
    <div className="min-h-screen bg-deep-navy">
      <div className="max-w-2xl mx-auto px-6 pt-20 pb-16 lg:px-8">
        {/* Header */}
        <div className="mb-10">
          <span className="font-body text-[11px] font-medium tracking-[0.08em] text-soft-gold uppercase">
            Your preferences
          </span>
          <h1 className="mt-2 font-display italic text-warm-cream leading-[1.05]" style={{ fontSize: 'clamp(32px, 4vw, 44px)' }}>
            Settings
          </h1>
          <p className="mt-3 font-body text-[15px] text-muted-cream leading-[1.6]">
            Everything here stays on this device. Nothing is sent to our servers.
          </p>
        </div>

        {/* Appearance */}
        <section className="bg-dark-surface rounded-2xl border border-navy-mid p-6 md:p-8 mb-6">
          <h2 className="font-body text-[16px] font-semibold text-warm-cream">Appearance</h2>
          <p className="mt-1 font-body text-[13px] text-muted-cream leading-[1.5]">
            Choose the theme that reads best for you. Every trust signal and
            disclosure is checked for readability in both.
          </p>

          <div className="mt-5 flex flex-col sm:flex-row gap-4">
            <ThemePreview mode="dark" active={theme === 'dark'} onSelect={() => select('dark')} />
            <ThemePreview mode="light" active={theme === 'light'} onSelect={() => select('light')} />
          </div>
        </section>

        {/* Wallet Data */}
        <section className="bg-dark-surface rounded-2xl border border-navy-mid p-6 md:p-8">
          <h2 className="font-body text-[16px] font-semibold text-warm-cream">Your wallet data</h2>
          <p className="mt-1 font-body text-[13px] text-muted-cream leading-[1.5]">
            {entries.length} nonprofit{entries.length !== 1 ? 's' : ''} saved. All stored locally — download or delete anytime.
          </p>

          <div className="mt-5 space-y-3">
            <button
              onClick={() => setExportModal(true)}
              disabled={entries.length === 0}
              className="w-full flex items-center justify-between p-4 rounded-lg border border-soft-gold/40 hover:border-soft-gold/80 hover:bg-soft-gold/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="text-left">
                <p className="font-body text-sm font-semibold text-warm-cream">Export wallet</p>
                <p className="font-body text-xs text-muted-cream mt-1">
                  Download as JSON or CSV for backup or re-import
                </p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold group-hover:translate-x-1 transition-transform shrink-0">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>

            <button
              onClick={() => setDeleteModal(true)}
              disabled={entries.length === 0}
              className="w-full flex items-center justify-between p-4 rounded-lg border border-alert-amber/40 hover:border-alert-amber/80 hover:bg-alert-amber/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="text-left">
                <p className="font-body text-sm font-semibold text-warm-cream">Delete all data</p>
                <p className="font-body text-xs text-muted-cream mt-1">
                  Permanently remove all {entries.length} bookmark{entries.length !== 1 ? 's' : ''} and giving intents
                </p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-alert-amber shrink-0">
                <polyline points="3 6 5 4 21 4 23 6" />
                <line x1="19" y1="4" x2="19" y2="20" />
                <line x1="5" y1="4" x2="5" y2="20" />
                <line x1="10" y1="9" x2="10" y2="17" />
                <line x1="14" y1="9" x2="14" y2="17" />
              </svg>
            </button>
          </div>
        </section>

        {/* Privacy note */}
        <div className="mt-6 flex items-start gap-3 p-4 rounded-xl border border-navy-mid bg-dark-surface/60">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-soft-gold shrink-0 mt-0.5">
            <rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <p className="font-body text-[13px] text-muted-cream leading-[1.55]">
            Your preference and wallet data are saved in this browser only — the same way your bookmarks work. No account, no tracking, deletable anytime.
          </p>
        </div>
      </div>

      {exportModal && <ExportModal entries={entries} onClose={() => setExportModal(false)} />}
      {deleteModal && <DeleteModal entries={entries} onClose={() => setDeleteModal(false)} />}
    </div>
  )
}
