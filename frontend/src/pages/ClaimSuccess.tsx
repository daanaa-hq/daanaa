import { useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'

export default function ClaimSuccess() {
  usePageMeta('Page Claimed', 'Your nonprofit page is now live on Daanaa.')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const ein = searchParams.get('ein') || ''

  useEffect(() => {
    if (!ein) navigate('/for-nonprofits', { replace: true })
  }, [ein, navigate])

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-nav">
      <div className="max-w-[520px] mx-auto px-6 py-12">
        <ClaimProgressBar currentStep="success" />
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full bg-soft-gold text-deep-navy mx-auto mb-5 flex items-center justify-center text-2xl font-bold">✓</div>
          <h1 className="font-display italic text-deep-navy mb-3">
            Your changes are saved
          </h1>
          <p className="font-body text-lead text-cool-grey">
            Thank you for claiming your Daanaa page. Your mission and giving links update on daanaa.org
            within 24 hours — usually sooner.
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-light-cream p-8 space-y-4">
          <Link
            to={`/org/${ein}`}
            className="block w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-body-lg font-semibold rounded-xl hover:bg-bright-gold transition-colors text-center"
          >
            View your public page →
          </Link>
          <p className="text-center font-body text-label text-muted-cream -mt-1">
            (may still show your prior info until the next update)
          </p>
          <Link
            to="/member/benefits"
            className="block w-full px-4 py-3 border border-soft-gold/40 text-deep-navy font-body text-body font-semibold rounded-xl hover:bg-soft-gold/8 transition-colors text-center"
          >
            Access guild benefits →
          </Link>
          <Link
            to="/"
            className="block w-full px-4 py-3 border border-light-cream text-deep-navy font-body text-body font-semibold rounded-xl hover:bg-light-cream transition-colors text-center"
          >
            Return home
          </Link>
          <p className="text-center font-body text-caption text-muted-cream pt-2">
            Questions? <a href="mailto:orgs@daanaa.org" className="text-soft-gold hover:underline">orgs@daanaa.org</a>
          </p>
        </div>
      </div>
    </div>
  )
}
