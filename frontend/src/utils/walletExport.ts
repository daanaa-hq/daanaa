import type { WalletEntry } from '../types/wallet'

/**
 * Export wallet as JSON: machine-readable, portable, preserves all data structure.
 * Includes timestamp and count for transparency.
 */
export function exportWalletAsJSON(entries: WalletEntry[]): string {
  const exportData = {
    exportedAt: new Date().toISOString(),
    version: '1.0',
    entryCount: entries.length,
    entries,
  }
  return JSON.stringify(exportData, null, 2)
}

/**
 * Export wallet as CSV: human-readable in Excel/Sheets.
 * One row per org; includes bookmark status and actual activity.
 */
export function exportWalletAsCSV(entries: WalletEntry[]): string {
  const headers = ['Organization EIN', 'Bookmarked At', 'In Donation List', 'Donations Count', 'Last Donation', 'In Volunteer List', 'Volunteer Hours', 'Last Volunteer Date']
  const rows = entries.map(e => [
    e.ein,
    new Date(e.bookmarkedAt).toLocaleDateString(),
    e.inFunding ? 'Yes' : 'No',
    e.donations?.length || 0,
    e.donations?.[e.donations.length - 1]?.date || '',
    e.inVolunteering ? 'Yes' : 'No',
    (e.volunteerHours?.reduce((sum, vh) => sum + vh.hours, 0) || 0).toFixed(1),
    e.volunteerHours?.[e.volunteerHours.length - 1]?.date || '',
  ])

  // CSV escape: wrap in quotes if contains comma, newline, or quote
  const escape = (v: string | number | boolean | undefined): string => {
    if (v === undefined || v === null) return ''
    const s = String(v)
    if (s.includes(',') || s.includes('\n') || s.includes('"')) {
      return `"${s.replace(/"/g, '""')}"`
    }
    return s
  }

  const csv = [
    headers.map(escape).join(','),
    ...rows.map(r => r.map(escape).join(',')),
  ].join('\n')
  return csv
}

/**
 * Trigger a file download in the browser.
 */
export function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Clear all wallet data from localStorage.
 * This is the destructive operation — ensure user confirmation before calling.
 */
export function deleteWalletData() {
  // Clear all wallet-related keys
  const keysToRemove = [
    'dw_entries',        // main entries
    'dw_kh',             // key hash
    'dw_s',              // salt
    'dw_sync_server',    // sync status
    'giving-wallet',     // legacy key (GivingListContext)
    'giving-list',       // legacy key
  ]
  keysToRemove.forEach(key => localStorage.removeItem(key))
}

/**
 * Get a human-readable summary of what will be deleted.
 */
export function getDeleteSummary(entries: WalletEntry[]): { bookmarks: number; donations: number; volunteerRecords: number } {
  const donations = entries.reduce((sum, e) => sum + (e.donations?.length || 0), 0)
  const volunteerRecords = entries.reduce((sum, e) => sum + (e.volunteerHours?.length || 0), 0)
  return {
    bookmarks: entries.length,
    donations,
    volunteerRecords,
  }
}
