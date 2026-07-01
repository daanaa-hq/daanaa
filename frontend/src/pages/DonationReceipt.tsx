import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

interface DonationRecord {
  id: string
  org_name: string
  ein: string
  amount: number
  date: string
  donor_name?: string
}

export default function DonationReceipt() {
  usePageMeta('Donation Receipt | Daanaa', 'Download your tax-deductible donation receipt')

  const [searchParams] = useSearchParams()
  const [donation, setDonation] = useState<DonationRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const donationId = searchParams.get('id')

  useEffect(() => {
    const fetchDonation = async () => {
      if (!donationId) {
        setError('No donation ID provided')
        setLoading(false)
        return
      }

      try {
        const wallet = localStorage.getItem('daanaa_wallet')
        if (!wallet) {
          throw new Error('No wallet found')
        }

        const walletData = JSON.parse(wallet)
        const donations = walletData.donations || []
        const found = donations.find((d: DonationRecord) => d.id === donationId)

        if (!found) {
          throw new Error('Donation not found')
        }

        setDonation(found)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    fetchDonation()
  }, [donationId])

  const handleDownload = async () => {
    if (!donation) return

    setDownloading(true)
    try {
      const response = await fetch('/api/wallet/donation-receipt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          donation_id: donation.id,
          org_name: donation.org_name,
          ein: donation.ein,
          amount: donation.amount,
          date: donation.date,
          donor_name: donation.donor_name || 'Honored Donor',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate receipt')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `donation_receipt_${donation.ein}_${donation.date.split('T')[0]}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-soft-cream p-6 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !donation) {
    return (
      <div className="min-h-screen bg-soft-cream p-6">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700 text-center">
            <p className="font-semibold mb-2">Unable to Load Receipt</p>
            <p>{error || 'Donation record not found'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-soft-cream p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-3xl text-deep-navy mb-2">Donation Receipt</h1>
          <p className="text-cool-grey">Tax-deductible donation documentation</p>
        </div>

        <div className="bg-white rounded-lg p-8 border border-light-grey space-y-6">
          <div className="bg-soft-cream rounded p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-cool-grey uppercase tracking-wide">Organization</p>
                <p className="font-display text-xl text-deep-navy">{donation.org_name}</p>
                <p className="text-sm text-cool-grey">EIN: {donation.ein}</p>
              </div>

              <div>
                <p className="text-xs text-cool-grey uppercase tracking-wide">Donation Amount</p>
                <p className="font-display text-xl text-link-gold">
                  ${donation.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
                <p className="text-sm text-cool-grey">
                  {new Date(donation.date).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          <div className="border-t border-light-grey pt-6">
            <h2 className="text-sm font-semibold text-deep-navy mb-3">Tax Documentation</h2>
            <div className="space-y-2 text-sm text-cool-grey">
              <p>✓ This donation is tax-deductible under IRS section 501(c)(3).</p>
              <p>
                ✓ No goods or services were provided in return for this donation.
              </p>
              <p>
                ✓ This receipt documents your contribution for tax purposes. Please retain for your
                records.
              </p>
            </div>
          </div>

          {donation.donor_name && donation.donor_name !== 'Honored Donor' && (
            <div className="border-t border-light-grey pt-6">
              <p className="text-sm text-cool-grey mb-2">Donor: {donation.donor_name}</p>
            </div>
          )}

          <div className="border-t border-light-grey pt-6">
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="w-full py-3 rounded-lg bg-soft-gold text-deep-navy font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
            >
              {downloading ? 'Generating PDF...' : '↓ Download PDF Receipt'}
            </button>
            <p className="text-xs text-cool-grey text-center mt-3">
              Your PDF receipt will include the IRS-compliant letter for your records.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-xs text-blue-700">
              <span className="font-semibold">Privacy Note:</span> This receipt is generated locally and
              stored only in your Giving Wallet. Daanaa does not retain copies of donation receipts.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
